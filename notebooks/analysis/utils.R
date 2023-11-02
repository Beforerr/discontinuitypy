library(ggplot2)
library(ggpubr)
library(patchwork)

library(see)

library(glue)
library(arrow)

# Save the plot, if filename is provided
save_plot <- function(filename = NULL) {
  if (!is.null(filename)) {
    ggsave(filename = glue("../figures/{filename}.png"))
    ggsave(filename = glue("../figures/{filename}.pdf"))
  }
}