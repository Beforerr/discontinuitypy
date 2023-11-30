if (!requireNamespace("ggdensity", quietly = TRUE))
  pak::pkg_install("ggdensity")
if (!requireNamespace("gaussplotR", quietly = TRUE))
  pak::pkg_install("gaussplotR")

library(dplyr)

library(ggplot2)
library(ggdensity)
library(ggpubr)
library(patchwork)
library(see)

library(glue)
library(arrow)
library(gaussplotR)
library(scales)

# Save the plot, if filename is provided
save_plot <- function(filename = NULL) {
  if (!is.null(filename)) {
    ggsave(filename = glue("../figures/{filename}.png"))
    ggsave(filename = glue("../figures/{filename}.pdf"))
  }
}


# Plotting function for Level 1 data.
# Similar to the `geom_bin2d` function, but with added functionality
# - Normalize the data to every x-axis value
# - Add peak values
# - Add mean values with error bars

library(scales)
# Helper function to calculate summary statistics for x-binned data
calculate_summary <- function(data, x_col, y_col, x_seq) {
  data %>%
    mutate(!!x_col := x_seq[findInterval(data[[x_col]], x_seq, rightmost.closed = TRUE)]) %>%
    group_by(.data[[x_col]]) %>%
    summarise(
      mean_y = mean(.data[[y_col]], na.rm = TRUE),
      sd_y = sd(.data[[y_col]], na.rm = TRUE),
      # se_y = sd_y / sqrt(n())
    )
}


plot_binned_data <- function(data, x_col, y_col, x_bins, y_bins, y_lim = NULL, log_y = FALSE) {
  # If y_lim is provided, filter the data
  if (!is.null(y_lim)) {
    data <- data %>%
      filter(.data[[y_col]] >= y_lim[1], .data[[y_col]] <= y_lim[2])
  }

  # If transform_log_y is TRUE, transform y_col to log scale
  if (log_y) {
    data[[y_col]] <- log10(data[[y_col]])
  }

  # Define bins for x and y based on the input parameters
  x_seq <- seq(min(data[[x_col]]), max(data[[x_col]]), length.out = x_bins + 1)
  y_seq <- seq(min(data[[y_col]]), max(data[[y_col]]), length.out = y_bins + 1)

  data_binned_normalized <- data %>%
    mutate(
      !!x_col := x_seq[findInterval(data[[x_col]], x_seq, rightmost.closed = TRUE, )],
      !!y_col := y_seq[findInterval(data[[y_col]], y_seq, rightmost.closed = TRUE, )]
    ) %>%
    count(!!sym(x_col), !!sym(y_col)) %>%
    group_by(!!sym(x_col)) %>%
    mutate(n = n / sum(n))

  plot <- ggplot() +
    geom_tile(data = data_binned_normalized, aes(x = .data[[x_col]], y = .data[[y_col]], fill = n))

  # Calculate mode for each x-bin
  modes <- data_binned_normalized %>%
    group_by(.data[[x_col]]) %>%
    slice_max(n, n = 1)

  # Add the mode line
  plot <- plot + geom_line(data = modes, aes(x = .data[[x_col]], y = .data[[y_col]], group = 1), linetype = "dashed")

  data_xbinned <- calculate_summary(data, x_col, y_col, x_seq)

  plot <- plot +
    geom_errorbar(data = data_xbinned, aes(x = .data[[x_col]], ymin = mean_y - sd_y, ymax = mean_y + sd_y)) +
    geom_line(data = data_xbinned, aes(x = .data[[x_col]], y = mean_y))

  # Note: ggline will produce another figure, so we use geom_line instead

  plot <- plot +
    scale_fill_viridis_c() +
    theme_pubr(base_size = 16, legend = "r")

  return(plot)
}



plot_dist <- function(
    y, ylab, y_lim = NULL, y_log = TRUE, x_bins = 8, y_bins = 16) {
  log_y <- y_log

  x_col <- "radial_distance"
  xlab <- "Radial Distance (AU)"
  p1 <- plot_binned_data(JNO_events_l1,
    x_col = x_col, y_col = y,
    x_bins = x_bins, y_bins = y_bins, y_lim = y_lim, log_y = log_y
  ) + labs(x = xlab, y = ylab) + ggtitle("JUNO")

  x_col <- "time"
  xlab <- "Time"
  p2 <- plot_binned_data(other_events_l1,
    x_col = x_col, y_col = y,
    x_bins = x_bins, y_bins = y_bins, y_lim = y_lim, log_y = log_y
  ) + labs(x = xlab, y = ylab) + ggtitle("Others")

  p <- p1 / p2
  return(p)
}