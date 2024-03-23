# RUN JONSM FIRST TO LOAD DATA - at least up until lone 27


# Replace locations across raw data
##################################################################

nd = clf %>% 
  filter(animal_id != "Both") %>%
  filter(date >= date("2022-05-12") & date <= date("2022-06-17"))

nd$dataset = 1  

all_locs = colnames(dd)[4:14]

replace_aid_df = function(df, rplp){
  ndf = df %>%
    mutate(rand_num = runif(dim(df)[1]),
           dataset = rplp) %>%
    mutate(location = case_when(
      rand_num > rplp ~ sample(all_locs, 1),
      TRUE ~ location
    )) %>%
    mutate(changed = rand_num > rplp) %>%
    select(-rand_num)
  return(ndf)
}

nnd = data.frame()
for (rnr_rp in seq(0.1,1, 0.1)){
  print(rnr_rp)
  nnd = rbind(nnd,
              replace_aid_df(nd, rnr_rp))
}

ndd = nnd %>% 
  select(date, animal_id, location, dataset) %>%
  #recoding location grouping replacable enrichment to one group
  mutate(location = case_when(
    location %in% c("other",  "back_left_balcony", "top_balcony",
                    "back_right_floor", "back_left_floor", "mid_balcony",
                    "back_right_balcony", "front_left_floor", 
                    "front_right_floor", "front_balcony") ~ location,
    TRUE ~ "enrichment")
  ) %>%
  group_by(date, animal_id, dataset) %>%
  reframe(tot_count = n(),
          location = location) %>%
  group_by(date, animal_id, location, dataset) %>%
  reframe(prob_l = n()/tot_count) %>%
  distinct() %>%
  mutate(event = case_when(
    date <= date("2022-05-16") ~ "surgery",
    date <= date("2022-05-22") ~ "jacket",
    date <= date("2022-05-25") ~ "recovery",
    date <= date("2022-05-31") ~ "pt",
    date <= date("2022-06-05") ~ "fight",
    date <= date("2022-06-17") ~ "control",
    date > date("2022-06-17") ~ "new_environment",
    TRUE ~ "other"
  )) %>%
  pivot_wider(names_from = location, values_from = prob_l) %>%
  replace(is.na(.), 0)



ndd1 = ndd %>% filter(animal_id == "Bracken")

ndd1$date_set = paste(ndd1$date,as.character(ndd1$dataset), sep="_")

ndm1 = KL(data.matrix(data.frame(ndd1[,5:15])))
row.names(ndm1) = as.character(ndd1$date_set)
colnames(ndm1) = as.character(ndd1$date_set)

diag(ndm1) = NA



ndf_brck = data.frame()

for (e in unique(ndd1$event)){
  for (ds in unique(ndd1$dataset)){
    rnr_ev = which(ndd1$event == e & ndd1$dataset == ds)
    rnr_cnt = which(ndd1$event == "control" & ndd1$dataset == ds)
    ndf_brck = rbind(ndf_brck, 
                     data.frame(
                       Event = e,
                       Dataset = ds,
                       KL_divergence = c(ndm1[rnr_ev, rnr_cnt])
                     )
    )
  }
}

ndf_brck$animal_id = "Bracken"

ndd2 = ndd %>% filter(animal_id == "Bramble")


ndd2$date_set = paste(ndd2$date,as.character(ndd2$dataset), sep="_")

ndm2 = KL(data.matrix(data.frame(ndd2[,5:15])))
row.names(ndm2) = as.character(ndd2$date_set)
colnames(ndm2) = as.character(ndd2$date_set)

diag(ndm2) = NA



ndf_brmbl = data.frame()

for (e in unique(ndd2$event)){
  for (ds in unique(ndd2$dataset)){
    rnr_ev = which(ndd2$event == e & ndd2$dataset == ds)
    rnr_cnt = which(ndd2$event == "control" & ndd2$dataset == ds)
    ndf_brmbl = rbind(ndf_brmbl, 
                      data.frame(
                        Event = e,
                        Dataset = ds,
                        KL_divergence = c(ndm2[rnr_ev, rnr_cnt])
                      )
    )
  }
}

ndf_brmbl$animal_id = "Bramble"

ndf_brck = ndf_brck %>%
  group_by(animal_id, Dataset) %>%
  mutate(
    mcntrl = mean(KL_divergence[which(Event == "control")], na.rm = TRUE),
    uppcntrl = mean_ci(KL_divergence[which(Event == "control")], ci = .95)[,3],
    lwcntrl = mean_ci(KL_divergence[which(Event == "control")], ci = .95)[,2],
  )

ndf_brmbl = ndf_brmbl %>%
  group_by(animal_id, Dataset) %>%
  mutate(
    mcntrl = mean(KL_divergence[which(Event == "control")], na.rm = TRUE),
    uppcntrl = mean_ci(KL_divergence[which(Event == "control")], ci = .95)[,3],
    lwcntrl = mean_ci(KL_divergence[which(Event == "control")], ci = .95)[,2],
  )

ndf_both = rbind(ndf_brck, ndf_brmbl)


ndf_both$aid_ds = paste(ndf_both$animal_id, ndf_both$Dataset, sep="_")
ndf_both %>%
  filter(Dataset>=0.6) %>%
  ggplot(aes(Event, KL_divergence, group = aid_ds)) +
  
  facet_grid(Dataset~animal_id) +
  
  geom_hline(aes(yintercept = mcntrl, group = aid_ds),
             linetype = "dashed", size = 0.7) +
  geom_hline(aes(yintercept = lwcntrl, group = aid_ds),
             linetype = "dashed", color = "grey", size = 0.7) +
  geom_hline(aes(yintercept = uppcntrl, group = aid_ds),
             linetype = "dashed", color = "grey", size = 0.7) +
  
  stat_summary(geom="point", fun.y=mean, size = 3) +
  stat_summary(fun.data = mean_se, geom = "errorbar", width = 0.2) + 
  
  theme_classic() +
  scale_x_discrete(limits = c('surgery', 'jacket', 'recovery',
                              'pt', 'fight', 'control'))


nanova_all = ndf_both %>% ungroup() %>%
  filter(Dataset == 0.6) %>%
  aov(KL_divergence ~ Event * animal_id, data = .)
summary(nanova_all)
TukeyHSD(anova_all, which = "Event")$Event[1:6,]
TukeyHSD(anova_all, which = "animal_id")





