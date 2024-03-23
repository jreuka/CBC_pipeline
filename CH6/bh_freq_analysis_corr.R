library(ggplot2)
library(dplyr)
library(lubridate)
library(stringr)
library(ggpubr)
library(tidyr)
library(lmerTest)
library(psych)
library(lsmeans)
#function to z-score a vector 
zscore = function(a){
  return((a-mean(a, na.rm=T))/sd(a, na.rm = T))
}

#read in detection data 
ff = read.csv("pers_resampled_500ms.csv")
#read in personality data
pt = read.csv("Animal_PersTraits.csv") %>%
  select(!X)

#recode variables
ff$datetime = as.POSIXct(ff$datetime,"%Y-%m-%d %H:%M:%S:%OS")
ff$date = date(ff$datetime)
ff$time = format(ff$datetime, format = "%H:%M:%S")
ff$hour = hour(ff$datetime)

#get camera module number
head(ff)
ff$cammod = str_split(ff$file_name, "_", simplify = TRUE)[,2]
unique(ff$cammod)

#recode animal ids
ff = ff %>%
  mutate(all_ids = case_when(
    cammod == 2 & animal_id == 2 ~ "Bloom",
    cammod == 2 & animal_id == 1 ~ "Brazil",
    cammod == 1 & date <= date("2021-08-17") & animal_id == 2 ~ "Malibu",
    cammod == 1 & date <= date("2021-08-17") & animal_id == 1 ~ "Custard",
    cammod == 1 & date >= date("2022-05-12") & animal_id == 1 ~ "Bramble",
    cammod == 1 & date >= date("2022-05-12") & animal_id == 2 ~ "Bracken",
    cammod == 3 & date <= date("2022-10-12") & animal_id == 2 ~ "Confetti",
    TRUE ~ "Undefined"
  ))

#code single housing
ff = ff %>%
  mutate(singly_housed = case_when(
    all_ids == "Custard" & date >= date("2021-07-27") ~ 1,
    all_ids == "Confetti" ~ 1, 
    TRUE ~ 0
  ))



# filter data
fff = ff %>% filter(all_ids != "Undefined")
fff$dupl = fff %>% select(file_name, datetime, all_ids, location) %>%
  duplicated(.)
clf = fff %>% filter(track_conf >= 0) %>%
  filter(dupl)


#code animals in same location
clf$soc1 = clf %>%
  select(file_name, datetime, location) %>%
  duplicated(.)

clf$soc2 = clf %>%
  select(file_name, datetime, location) %>%
  duplicated(., fromLast = T)

clf$soc = clf$soc1 | clf$soc2

clf = clf %>% select(-soc1, -soc2)

wpt = pivot_wider(pt, names_from = personality_trait, values_from = score)


ptf = left_join(clf, wpt, by = join_by("all_ids"=="animal_id"))

ptf = ptf %>%
  mutate(tod = case_when(
    hour <= 14 ~ "Noon",
    hour > 14 ~ "Evening"
  ))
ptf$date_tod = paste(ptf$date, ptf$tod, sep = "_")

v_q3 = quantile(ptf$velocity, prob=c(.75), na.rm = T)

ptf1 = ptf %>%
  group_by(all_ids, date_tod) %>%
  mutate(freq_vel = sum(velocity>=v_q3, na.rm = T)/n())


ptf2 = ptf1 %>%
  group_by(all_ids, date_tod) %>%
  mutate(freq_locchange = (length(rle(location)$values)-1)/n())


unique(ptf2$location)

ptf3 = ptf2 %>%
  mutate(elevated = case_when(
    location %in% c("front_left_floor", "front_right_floor",
                    "back_left_floor", "back_right_floor") ~ 1,
    TRUE ~ 0
  ))

ptf3 = ptf3 %>%
  group_by(all_ids, date_tod) %>%
  mutate(frq_elevated = sum(elevated)/n())



unique(ptf3$location)

ptf4 = ptf3 %>%
  mutate(front_c = case_when(
    location %in% c("front_left_floor", "front_right_floor",
                    "front_balcony", "left_enrichment_tire",
                    "left_enrichment_pole", "left_enrichment_house",
                    "left_hose", "left_enrichment_tube") ~ 1,
    TRUE ~ 0
  ))


ptf4 = ptf4 %>%
  group_by(all_ids, date_tod) %>%
  mutate(frq_front = sum(front_c)/n())


ptf5 = ptf4 %>%
  group_by(all_ids, date_tod) %>%
  mutate(frq_soc = sum(soc)/sum(!singly_housed))



frq_vals = ptf5 %>%
  select(animal_id, date_tod,
         freq_vel, freq_locchange, frq_elevated, frq_front, frq_soc) %>%
  distinct()

write.csv(frq_vals, "frequencyBH_animals.csv")

######
library(pander)
library(corrplot)

ptf5[1,c(25:30, 33, 34, 36, 38, 39)]
ct = corr.test(ptf5[,c(25:30, 33, 34, 36, 38, 39)],method = "spearman", adjust = "holm")

ct %>% pander()

ct$r[7:11,1:6]

ct_r = ct$r[7:11,1:6]
rownames(ct_r) = c("high_velocity_frequency",
                   "location_change_frequency",
                   "elevated_frequency",
                   "front_cage_frequency",
                   "social_proximity_frequency")

ct_padj = matrix(ct$p.adj[c(6:10,15:19,23:27,30:34,36:45)], nrow = 5, ncol = 6)
colnames(ct_padj) = colnames(ct_r)
rownames(ct_padj) = rownames(ct_r)



corrplot(ct_r, method = "number")


corrplot(ct_r, method="color",
         addCoef.col = "black", # Add coefficient of correlation
         tl.col="black", tl.cex = 1.5, #Text label color and rotation
         # Combine with significance
         p.mat = ct_padj, sig.level = 0.01, insig = "blank",
         cl.pos = "n", number.digits = 2, number.cex = 1.2
)
ct_padj


corrplot(ct$r, method="color",
         addCoef.col = "black", # Add coefficient of correlation
         tl.col="black", tl.cex = 1.5, #Text label color and rotation
         # Combine with significance
         p.mat = ct$p, sig.level = 0.01, insig = "blank",
         cl.pos = "n", number.digits = 2, number.cex = 1.2
)



#ptf5[,c(25:30)]
ct_tr = corr.test(wpt[,2:7],method = "spearman", adjust = "holm")

corrplot(ct_tr$r, method="color",
         addCoef.col = "black", # Add coefficient of correlation
         tl.col="black", tl.cex = 1.5, #Text label color and rotation
         # Combine with significance
         p.mat = ct_tr$p, sig.level = 0.05, insig = "blank",
         cl.pos = "n", number.digits = 2, number.cex = 1.2
)




ptf5 %>%
  ungroup() %>%
  filter(all_ids != "Bloom") %>%
  select(all_ids, Confidence, Openness, Dominance,
         Friendliness, Activity, Anxiety,
         freq_vel, freq_locchange, frq_elevated, frq_front, frq_soc) %>%
  pivot_longer(!c(all_ids,freq_vel, freq_locchange, frq_elevated, frq_front, frq_soc),
               names_to = "Trait", values_to = "score") %>%
  pivot_longer(!c(all_ids, Trait, score),
               names_to = "BH_measure", values_to = "frequency") %>%
  mutate(BH_measure = factor(BH_measure,
                             levels = c("freq_vel", "freq_locchange",
                                        "frq_elevated", "frq_front",
                                        "frq_soc")),
         Trait = factor(Trait, levels = c("Confidence", "Openness",
                                          "Dominance", "Friendliness",
                                          "Activity", "Anxiety"
                                          ))
         ) %>%
  #filter(Trait == pstt, BH_measure == bhm) %>%
  ggline(., x = "score", y = "frequency", color = "all_ids",
         add = c("mean_ci"),
         size=1, point.size = 0.1,  add.params = list(size = 1, alpha = 0.3),
         xlab = F, ylab = F,
         facet.by = c("BH_measure", "Trait"),
         panel.labs.background = list(fill = "white", color = "black"),
         numeric.x.axis = T,
         legend = "right")




####
#plotting behaviours
####
ptf5 %>%
  ungroup() %>%
  filter(all_ids != "Bloom") %>%
  select(all_ids,
         freq_vel, freq_locchange, frq_elevated, frq_front, frq_soc,
         tod) %>%
  pivot_longer(!c(all_ids, tod),
               names_to = "BH_measure", values_to = "frequency") %>%
  mutate(BH_measure = factor(BH_measure,
                             levels = c("freq_vel", "freq_locchange",
                                        "frq_elevated", "frq_front",
                                        "frq_soc"))) %>%
  distinct() %>%
  ggline(., x = "BH_measure", y = "frequency", color = "all_ids",
          add = c("mean_ci", "jitter"),
          size=1, point.size = 0.2,  add.params = list(size = 2, alpha = 0.3, 
                                                       shape = 19, width= 0.05),
          xlab = F, ylab = F,
          facet.by = c("tod"),
          panel.labs.background = list(fill = "white", color = "black"),
          numeric.x.axis = T,
          legend = "right")


aov_bhfrq = ptf5 %>%
  ungroup() %>%
  filter(all_ids != "Bloom") %>%
  select(all_ids,
         freq_vel, freq_locchange, frq_elevated, frq_front, frq_soc,
         tod) %>%
  pivot_longer(!c(all_ids, tod),
               names_to = "BH_measure", values_to = "frequency") %>%
  mutate(BH_measure = factor(BH_measure,
                             levels = c("freq_vel", "freq_locchange",
                                        "frq_elevated", "frq_front",
                                        "frq_soc"))) %>%
  distinct() %>%
  aov(frequency ~ BH_measure * all_ids * tod, data= . )

summary(aov_bhfrq)

