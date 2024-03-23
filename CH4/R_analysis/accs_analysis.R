library(dplyr)
library(tidyr)
library(stringr)
library(ggplot2)
library(ggpubr)
library(DescTools)

dd = read.csv("all_accs.csv")

dd = dd %>%
  mutate(test = str_split(source, "_", simplify = T)[,1])


dd %>%
  filter(test == "Long") %>%
  ggline(., x = "source", y = c("accs", "rec1", "rec2"),
         add = c("mean_ci"),
         size=1, point.size = 1,  add.params = list(size = 1, alpha = 0.3),
         xlab = F, ylab = F,
         combine = T)+
  geom_hline(yintercept = 0.5, col = "red", linetype = 2)

dd %>%
  filter(test == "Eq") %>%
  group_by(source) %>%
  mutate(
    Mean = mean_ci(accs)[1],
    Lower_CI = mean_ci(accs)[2],
    Upper_CI = mean_ci(accs)[3]
    # Median = MedianCI(accs)[1],
    # Lower_CI = MedianCI(accs)[2],
    # Upper_CI = MedianCI(accs)[3]
    ) %>%
  select(source, Mean, Lower_CI,  Upper_CI) %>%
  distinct()

dd %>%
  filter(test == "Eq") %>%
  group_by(source) %>%
  mutate(Mean1 = mean_ci(rec1)[1],
         Upper_CI1 = mean_ci(rec1)[3],
         Lower_CI1 = mean_ci(rec1)[2],
         # Median1 = MedianCI(rec1)[1],
         # Upper_mCI1 = MedianCI(rec1)[3],
         # Lower_mCI1 = MedianCI(rec1)[2],
         # Median2 = MedianCI(rec2)[1],
         # Upper_CI2 = MedianCI(rec2)[3],
         # Lower_CI2 = MedianCI(rec2)[2],
         Mean2 = mean_ci(rec2)[1],
         Upper_CI2 = mean_ci(rec2)[3],
         Lower_CI2 = mean_ci(rec2)[2]) %>%
  select(source, Mean1, Lower_CI1, Upper_CI1, Mean2, Lower_CI2,  Upper_CI2) %>%
  distinct()


dd %>%
  filter(test == "ar") %>%
  group_by(source) %>%
  mutate(
    Mean = mean_ci(accs)[1],
    Lower_CI = mean_ci(accs)[2],
    Upper_CI = mean_ci(accs)[3]
    # Median = MedianCI(accs)[1],
    # Lower_CI = MedianCI(accs)[2],
    # Upper_CI = MedianCI(accs)[3]
  ) %>%
  select(source, Mean, Lower_CI,  Upper_CI) %>%
  distinct()


dd %>%
  filter(test == "ar") %>%
  group_by(source) %>%
  mutate(Mean1 = mean_ci(rec1)[1],
         Upper_CI1 = mean_ci(rec1)[3],
         Lower_CI1 = mean_ci(rec1)[2],
         # Median1 = MedianCI(rec1)[1],
         # Upper_mCI1 = MedianCI(rec1)[3],
         # Lower_mCI1 = MedianCI(rec1)[2],
         # Median2 = MedianCI(rec2)[1],
         # Upper_CI2 = MedianCI(rec2)[3],
         # Lower_CI2 = MedianCI(rec2)[2],
         Mean2 = mean_ci(rec2)[1],
         Upper_CI2 = mean_ci(rec2)[3],
         Lower_CI2 = mean_ci(rec2)[2]) %>%
  select(source, Mean1, Lower_CI1, Upper_CI1, Mean2, Lower_CI2,  Upper_CI2) %>%
  distinct()




dd %>%
  filter(test == "Eq") %>%
  ggline(., x = "source", y = c("accs", "rec1", "rec2"),
         add = c("mean_ci"),
         size=1, point.size = 1,  add.params = list(size = 1, alpha = 0.3),
         xlab = F, ylab = F,
         combine = T)+
  geom_hline(yintercept = 0.5, col = "red", linetype = 2)


dd %>%
  filter(test == "Dates") %>%
  select(source, accs, accs_d2, accs_d3) %>%
  pivot_longer(!source, names_to = "Measure", values_to = "accs") %>%
  ggline(., x = "source", y = "accs", color = "Measure",
         add = c("mean_ci"),
         size=1, point.size = 1,  add.params = list(size = 1, alpha = 0.3),
         xlab = F, ylab = F,
         combine = T,
         legend = "right")+
  geom_hline(yintercept = 0.5, col = "red", linetype = 2)


dd %>%
  filter(test == "Dates") %>%
  group_by(source) %>%
  summarise(Mean_D1 = mean_ci(accs)[1],
         Lower_D1 = mean_ci(accs)[2],
         Upper_D1 = mean_ci(accs)[3],
         Mean_D2 = mean_ci(accs_d2)[1],
         Lower_D2 = mean_ci(accs_d2)[2],
         Upper_D2 = mean_ci(accs_d2)[3],
         Mean_D3 = mean_ci(accs_d3)[1],
         Lower_D3 = mean_ci(accs_d3)[2],
         Upper_D3 = mean_ci(accs_d3)[3],
         )







