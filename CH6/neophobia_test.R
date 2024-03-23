# RUN bh_freq_analysis up untill line 59
library(ggplot2)
library(dplyr)
library(lubridate)
library(stringr)
library(ggpubr)
library(tidyr)
library(psych)
library(corrplot)
library(lme4)

zscore = function(a){
  return((a-mean(a, na.rm=T))/sd(a, na.rm = T))
}


tt = read.csv("Temp_test_data_14_12_22.csv")

unique(tt$Animal_ID)
unique(pt$animal_id)

str_to_upper(unique(fff$all_ids))

ttp = tt %>%
  filter(Animal_ID %in% str_to_upper(unique(fff$all_ids))) %>%
  select(Animal_ID, Age_Wean, Phase, behind_visual_barrier, approach_latency_2,
         freeze, escape_attempt) %>%
  group_by(Animal_ID) %>%
  mutate(s_bvb = sum(behind_visual_barrier),
         s_fr = sum(freeze),
         s_ea = sum(escape_attempt)) %>%
  ungroup() %>%
  select(!c(behind_visual_barrier, freeze, escape_attempt)) %>%
  pivot_wider(names_from = Phase,
              values_from = approach_latency_2) %>%
  mutate(z_bvb = zscore(s_bvb),
         z_ap_FF = zscore(FF),
         z_ap_NF = zscore(NF),
         z_ap_NO1 = zscore(NO1),
         z_ap_NO2 = zscore(NO2),
         z_fr = zscore(s_fr),
         z_ea = zscore(s_ea)) %>%
  select(Animal_ID, Age_Wean, z_bvb, z_ap_FF, z_ap_NF, z_ap_NO1,  z_ap_NO2,
         z_fr, z_ea)


head(ttp)

ttpca = principal(ttp[,3:9], nfactors = 1, rotate = "varimax")

print(ttpca)


ttp$PC1 = ttpca$scores

ttpca2 = principal(ttp[,c(3,4,6:8)], nfactors = 1, rotate = "varimax")

print(ttpca2)


ttp$PC2 = ttpca2$scores[,1]
colnames(ttp)

ttp1 = pt %>%
  mutate(Animal_ID = str_to_upper(animal_id)) %>%
  select(!animal_id) %>%
  pivot_wider(names_from = personality_trait, values_from = score) %>%
  merge(., ttp, by="Animal_ID")


cr_ttp = corr.test(ttp1[,c(2:7, 16, 17)] ,method = "spearman", adjust = "holm")

corrplot(cr_ttp$r, method="color",
         addCoef.col = "black", # Add coefficient of correlation
         tl.col="black", tl.cex = 1.5, #Text label color and rotation
         # Combine with significance
         p.mat = cr_ttp$p, sig.level = 0.05, insig = "blank",
         cl.pos = "n", number.digits = 2, number.cex = 1.2
)
cr_ttp$p


##### BH
frq_vals = read.csv("frequencyBH_animals.csv")

fv1 = frq_vals %>%
  ungroup() %>%
  mutate(Animal_ID = str_to_upper(all_ids)) %>%
  filter(Animal_ID %in% unique(ttp1$Animal_ID)) %>%
  select(!c(all_ids, animal_id))


fv2 = ttp1 %>%
  select(Animal_ID, Confidence, Openness, Dominance, Friendliness,
         Activity, Anxiety, Age_Wean, PC1, PC2) %>%
  merge(., fv1, by="Animal_ID")

colnames(fv2)
cr_ftp = corr.test(fv2[,c(2:7,9,10,12:16)])

corrplot(cr_ftp$r, method="color",
         addCoef.col = "black", # Add coefficient of correlation
         tl.col="black", tl.cex = 1.5, #Text label color and rotation
         # Combine with significance
         #p.mat = cr_ftp$p, sig.level = 0.05, insig = "blank",
         cl.pos = "n", number.digits = 2, number.cex = 1.2
)

