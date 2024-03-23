library(ggplot2)
library(lubridate)
library(dplyr)
library(tidyr)
library(philentropy)
library(ggpubr)
library(stringr)
library(lsmeans)

stderror <- function(x) sd(x, na.rm = TRUE)/sqrt(sum(!is.na(x)))


ff = read.csv("BrBr_202206_resampled_500ms.csv")

ff$datetime = as.POSIXct(ff$datetime,"%Y-%m-%d %H:%M:%S:%OS")
ff$date = date(ff$datetime)
ff$time = format(ff$datetime, format = "%H:%M:%S")
ff$hour = hour(ff$datetime)

ff$dupl = ff %>% select(file_name, datetime, animal_id, location) %>%
  duplicated(.)

fff = ff %>% filter(dupl & date>= date("2022-05-12")) 

clf = fff %>% filter(track_conf >= 0) %>%
  mutate(animal_id = recode_factor(animal_id, '1'='Bramble', '2'='Bracken'))


dates = unique(fff$date)

################################
# Kullback-Leibler Divergence

#calculate location probability distribution per day
dd = clf %>%
  select(date, animal_id, location) %>%
  #recoding location grouping replacable enrichment to one group
  mutate(location = case_when(
    location %in% c("other",  "back_left_balcony", "top_balcony",
                    "back_right_floor", "back_left_floor", "mid_balcony",
                    "back_right_balcony", "front_left_floor", 
                    "front_right_floor", "front_balcony") ~ location,
    TRUE ~ "enrichment")
  ) %>%
  group_by(date, animal_id) %>%
  reframe(tot_count = n(),
          location = location) %>%
  group_by(date, animal_id, location) %>%
  reframe(prob_l = n()/tot_count) %>%
  distinct() %>%
  mutate(event = case_when(
    date <= date("2022-05-16") ~ "surgery",
    date <= date("2022-05-22") ~ "jacket",
    date <= date("2022-05-25") ~ "recovery",
    date <= date("2022-05-31") ~ "pt",
    date <= date("2022-06-05") ~ "fight",
    date <= date("2022-06-17") ~ "control",
    TRUE ~ "other"
  )) %>%
  pivot_wider(names_from = location, values_from = prob_l) %>%
  replace(is.na(.), 0)


dd1 = dd %>%
  filter(animal_id == "Bracken")


dm1 = KL(data.matrix(data.frame(dd1[,4:14])))
row.names(dm1) = as.character(dd1$date)
colnames(dm1) = as.character(dd1$date)


dm_kl_brck = dm1
diag(dm_kl_brck) = NA


dates = dd1$date

sg = which(dates <= date("2022-05-16") & dates > date("2021-06-05")) # surgery
jck = which(dates > date("2022-05-16") & dates <= date("2022-05-22")) # jacket
rcv = which((dates > date("2022-05-22") & dates <= date("2022-05-25")) )# recovery
pt = which(dates > date("2022-05-25") & dates <= date("2022-05-31")) # pt
ft = which(dates > date("2022-05-31") & dates <= date("2022-06-05")) # fight
cnt = which(dates >= date("2022-06-06") & dates <= date("2022-06-17"))  # control

#####
#Bracken
#####
df_brck <- rbind(
  data.frame(
    Event = "EMG",
    KL_divergence = c(dm_kl_brck[sg,cnt])
  ),
  data.frame(
    Event = "jacket",
    KL_divergence = c(dm_kl_brck[jck,cnt])
  ),
  data.frame(
    Event = "recovery",
    KL_divergence = c(dm_kl_brck[rcv,cnt])
  ),
  data.frame(
    Event = "PT",
    KL_divergence = c(dm_kl_brck[pt,cnt])
  ),
  data.frame(
    Event = "fight",
    KL_divergence = c(dm_kl_brck[ft,cnt])
  ),
  data.frame(
    Event = "control",
    KL_divergence = c(dm_kl_brck[cnt,cnt])
  )
)

#####
#Bramble
#####

#####
dd2 = dd %>%
  filter(animal_id == "Bramble")

dm2 = KL(data.matrix(data.frame(dd2[,4:14])))
row.names(dm2) = as.character(dd2$date)
colnames(dm2) = as.character(dd2$date)

dm_kl_brmb = dm2
diag(dm_kl_brmb) = NA


df_brmbl <- rbind(
  data.frame(
    Event = "EMG",
    KL_divergence = c(dm_kl_brmb[sg,cnt])
    ),
  data.frame(
    Event = "jacket",
    KL_divergence = c(dm_kl_brmb[jck,cnt])
  ),
  data.frame(
    Event = "recovery",
    KL_divergence = c(dm_kl_brmb[rcv,cnt])
  ),
  data.frame(
    Event = "PT",
    KL_divergence = c(dm_kl_brmb[pt,cnt])
  ),
  data.frame(
    Event = "fight",
    KL_divergence = c(dm_kl_brmb[ft,cnt])
  ),
  data.frame(
    Event = "control",
    KL_divergence = c(dm_kl_brmb[cnt,cnt])
  )
)


####
#both animals
#####

df_brck$animal_id = "Bracken"
df_brmbl$animal_id = "Bramble"
df_both = rbind(df_brck, df_brmbl) %>%
  mutate(Event = case_when(
    Event == "Bramble_control" ~ "other-animal-control",
    Event == "Bracken_control" ~ "other-animal-control",
    TRUE ~ Event
  ))


df_both %>%
  filter(Event != "new_environment") %>%
  ggline(., x = "Event", y = "KL_divergence", group = "animal_id",
         add = c("mean_ci"),
         size=1, add.params = list(size = 1, alpha = 0.3)) +
  
  geom_hline(yintercept = mean_ci(df_brck$KL_divergence[which(df_brck$Event == "control")])$y,
             linetype = 2,
             color = "blue") +
  geom_hline(yintercept = mean_ci(df_brck$KL_divergence[which(df_brck$Event == "control")])$ymin,
             linetype = 2,
             color="lightblue") +
  geom_hline(yintercept = mean_ci(df_brck$KL_divergence[which(df_brck$Event == "control")])$ymax,
             linetype = 2,
             color="lightblue") +
  
  geom_hline(yintercept = mean_ci(df_brmbl$KL_divergence[which(df_brmbl$Event == "control")])$y,
             linetype = 2,
             color = "green") +
  geom_hline(yintercept = mean_ci(df_brmbl$KL_divergence[which(df_brmbl$Event == "control")])$ymin,
             linetype = 2,
             color="lightgreen") +
  geom_hline(yintercept = mean_ci(df_brmbl$KL_divergence[which(df_brmbl$Event == "control")])$ymax,
             linetype = 2,
             color="lightgreen") +
  
  geom_hline(yintercept = mean_ci(df_both$KL_divergence[which(df_both$Event == "control" & df_both$animal_id=="Both")])$y,
             linetype = 2,
             color = "red") +
  geom_hline(yintercept = mean_ci(df_both$KL_divergence[which(df_both$Event == "control" & df_both$animal_id=="Both")])$ymin,
             linetype = 2,
             color="magenta") +
  geom_hline(yintercept = mean_ci(df_both$KL_divergence[which(df_both$Event == "control" & df_both$animal_id=="Both")])$ymax,
             linetype = 2,
             color="magenta") +
  facet_grid(animal_id~.)



anova_brck = df_both %>% 
  filter(animal_id == "Bracken") %>%
  aov(KL_divergence ~ Event, data = .)
summary(anova_brck)
TukeyHSD(anova_brck)$Event[1:6,]


anova_brmbl = df_both %>% 
  filter(animal_id == "Bramble") %>%
  aov(KL_divergence ~ Event, data = .)
summary(anova_brmbl)
TukeyHSD(anova_brmbl)$Event[1:7,]

anova_all = df_both %>%
  aov(KL_divergence ~ Event * animal_id, data = .)
summary(anova_all)
TukeyHSD(anova_all, which = c("Event", "animal_id"))
TukeyHSD(anova_all, which = "animal_id")


lsmeans(anova_all, pairwise ~ Event:animal_id, adjust = "tukey")

#######
# plot per day
#######

perdaydm_brck = dm_kl_brck[1:max(cnt),cnt]
colnames(perdaydm_brck) = c("cntrl1", "cntrl2", "cntrl3", "cntrl4",
                            "cntrl5", "cntrl6", "cntrl7", "cntrl8",
                            "cntrl9", "cntrl10", "cntrl11", "cntrl12")
pd_df_brck = data.frame(perdaydm_brck) %>%
  mutate(day = rownames(.)) %>%
  pivot_longer(!day, names_to = "control_day", values_to = "KL_Divergence") %>%
  mutate(animal_id = "Bracken")


perdaydm_brmbl = dm_kl_brmb[1:max(cnt),cnt]
colnames(perdaydm_brmbl) = c("cntrl1", "cntrl2", "cntrl3", "cntrl4",
                             "cntrl5", "cntrl6", "cntrl7", "cntrl8",
                             "cntrl9", "cntrl10", "cntrl11", "cntrl12")
pd_df_brmbl = data.frame(perdaydm_brmbl) %>%
  mutate(day = rownames(.)) %>%
  pivot_longer(!day, names_to = "control_day", values_to = "KL_Divergence") %>%
  mutate(animal_id = "Bramble")


ggline(pd_df_brck, x="day", y="KL_Divergence", group = "day",
       add = c("mean_ci"),
       size=1, add.params = list(size = 1, alpha = 0.3)) +
  theme(axis.text.x = element_text(angle=90)) +
  geom_hline(yintercept = mean_ci(df_brck$KL_divergence[which(df_brck$Event == "control")])$y,
             linetype = 2) +
  geom_hline(yintercept = mean_ci(df_brck$KL_divergence[which(df_brck$Event == "control")])$ymin,
             linetype = 2,
             color="grey") +
  geom_hline(yintercept = mean_ci(df_brck$KL_divergence[which(df_brck$Event == "control")])$ymax,
             linetype = 2,
             color="grey") +
  geom_vline(xintercept = "2022-05-12",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-05-17",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-05-22",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-05-26",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-06-01",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-06-05",
             linetype = 4, color="grey")

## plot probability distribution for day
dd %>% filter(animal_id == "Bramble" & event %in% c("surgery","jacket", "average_control")) %>%
  pivot_longer(!c(date, animal_id, event), names_to = "location", values_to = "Probability") %>%
  ggplot(aes(location, Probability)) +
  geom_bar(stat = "identity") +
  facet_grid(date~.) +
  theme_classic() +
  theme(strip.text.y = element_text(angle = 0))


ggline(pd_df_brmbl, x="day", y="KL_Divergence", group = "day",
       add = c("mean_ci"),
       size=1, add.params = list(size = 1, alpha = 0.3)) +
  theme(axis.text.x = element_text(angle=90)) +
  geom_hline(yintercept = mean_ci(df_brmbl$KL_divergence[which(df_brmbl$Event == "control")])$y,
             linetype = 2) +
  geom_hline(yintercept = mean_ci(df_brmbl$KL_divergence[which(df_brmbl$Event == "control")])$ymin,
             linetype = 2,
             color="grey") +
  geom_hline(yintercept = mean_ci(df_brmbl$KL_divergence[which(df_brmbl$Event == "control")])$ymax,
             linetype = 2,
             color="grey") +
  geom_vline(xintercept = "2022-05-12",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-05-17",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-05-22",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-05-26",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-06-01",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-06-05",
             linetype = 4, color="grey")




pd_df_both = rbind(pd_df_brck, pd_df_brmbl)

ggline(pd_df_both, x="day", y="KL_Divergence", group = "animal_id",
       add = c("mean_ci"),
       size=1, add.params = list(size = 1, alpha = 0.3)) +
  theme(axis.text.x = element_text(angle=90))+
  
  geom_hline(yintercept = mean_ci(df_brck$KL_divergence[which(df_brck$Event == "control")])$y,
             linetype = 2,
             color = "green") +
  geom_hline(yintercept = mean_ci(df_brck$KL_divergence[which(df_brck$Event == "control")])$ymin,
             linetype = 2,
             color="lightgreen") +
  geom_hline(yintercept = mean_ci(df_brck$KL_divergence[which(df_brck$Event == "control")])$ymax,
             linetype = 2,
             color="lightgreen") +
  
  geom_hline(yintercept = mean_ci(df_brmbl$KL_divergence[which(df_brmbl$Event == "control")])$y,
             linetype = 2,
             color = "blue") +
  geom_hline(yintercept = mean_ci(df_brmbl$KL_divergence[which(df_brmbl$Event == "control")])$ymin,
             linetype = 2,
             color="lightblue") +
  geom_hline(yintercept = mean_ci(df_brmbl$KL_divergence[which(df_brmbl$Event == "control")])$ymax,
             linetype = 2,
             color="lightblue") +
  
  geom_vline(xintercept = "2022-05-12",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-05-17",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-05-22",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-05-26",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-06-01",
             linetype = 4, color="grey") +
  geom_vline(xintercept = "2022-06-05",
             linetype = 4, color="grey") + 
  facet_grid(animal_id~.)




######
# Test Bracken Diazepam

br_dzp = pd_df_brck %>%
  filter(day >= date("2022-06-05")) %>%
  mutate(Diazepam = case_when(
    day %in% c(date("2022-06-07"),
               date("2022-06-08"),
               date("2022-06-09"),
               date("2022-06-10"),
               date("2022-06-13"),
               date("2022-06-15"),
               date("2022-06-16"),
               date("2022-06-17")) ~ T,
    TRUE ~ FALSE
  ))


br_dzp %>%
  ggplot(aes(Diazepam, KL_Divergence)) +
  geom_boxplot()


br_dzp %>%
  t.test(data=., KL_Divergence~Diazepam)


br_dzp %>%
  wilcox.test(data=., KL_Divergence~Diazepam)


mean_ci(br_dzp$KL_Divergence[which(br_dzp$Diazepam==FALSE)])
mean_ci(br_dzp$KL_Divergence[which(br_dzp$Diazepam==TRUE)])

library(DescTools)
MedianCI(br_dzp$KL_Divergence[which(br_dzp$Diazepam==FALSE)], na.rm = T)
MedianCI(br_dzp$KL_Divergence[which(br_dzp$Diazepam==TRUE)], na.rm = T)

br_dzp %>%
  ggline(., x="Diazepam", y= "KL_Divergence",
         add = c("mean_ci"),
         size=1, add.params = list(size = 1, alpha = 0.3))

