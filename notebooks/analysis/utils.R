pak::pkg_install("gaussplotR")

library(dplyr)

library(ggplot2)
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

# Helper function to calculate summary statistics for x-binned data
calculate_summary <- function(data, x_col, y_col, x_seq) {
  data %>%
    mutate(!!x_col := x_seq[findInterval(data[[x_col]], x_seq, rightmost.closed = TRUE)]) %>%
    group_by(!!sym(x_col)) %>%
    summarise(
      mean_y = mean(!!sym(y_col), na.rm = TRUE),
      sd_y = sd(!!sym(y_col), na.rm = TRUE),
      se_y = sd_y / sqrt(n())
    )
}


plot_binned_data <- function(
    data, x_col, y_col, x_bins, y_bins, y_lim = NULL, log_y = FALSE) {
  # If y_lim is provided, filter the data
  if (!is.null(y_lim)) {
    data <- data %>%
      filter(!!sym(y_col) >= y_lim[1], !!sym(y_col) <= y_lim[2])
  }

  # If transform_log_y is TRUE, transform y_col to log scale
  if (log_y) {
    data[[y_col]] <- log10(data[[y_col]])
    y_label <- paste("Log10", y_col)
  } else {
    y_label <- y_col
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
    geom_tile(data = data_binned_normalized, aes(x = !!sym(x_col), y = !!sym(y_col), fill = n))

  # Calculate mode for each x-bin
  modes <- data_binned_normalized %>%
    group_by(!!sym(x_col)) %>%
    slice_max(n, n = 1)

  # Add the mode line
  plot <- plot + geom_line(data = modes, aes(x = !!sym(x_col), y = !!sym(y_col), group = 1), linetype = "dashed")

  data_xbinned <- calculate_summary(data, x_col, y_col, x_seq)

  plot <- plot +
    geom_errorbar(data = data_xbinned, aes(x = !!sym(x_col), ymin = mean_y - sd_y, ymax = mean_y + sd_y), width = 0.2) +
    geom_line(data = data_xbinned, aes(x = !!sym(x_col), y = mean_y))
  # Note: ggline will produce another figure, so we use geom_line instead


  plot <- plot + labs(y = y_label) + # Set y-axis label
    scale_fill_viridis_c() +
    # scale_fill_viridis_c(trans = 'log', labels = label_number(accuracy = 0.001)) +
    theme_pubr(base_size = 16, legend = "r")

  return(plot)
}
