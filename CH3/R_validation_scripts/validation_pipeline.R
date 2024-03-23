library(dplyr)
library(ggplot2)
library(ggpattern)
library(tidyr)

#read in data
dd = read.csv("new_comparison.csv",)


# take head visible information from manually labelled data
dd = dd %>% group_by(file_name, frame_number) %>%
  mutate(head_visible = unique(head_visible[source == "labelled"])) %>%
  ungroup()

# clean up data
dd = dd %>% select(!X) %>%
  filter(!is.na(location)) %>%
  filter(location != "")

colnames(dd)

# check for duplicates - indicating matching predictions - overall
dd$dupl = dd %>%
  select(-source, -head_visible, -cam_match) %>%
  mutate(dupl = duplicated(.) | duplicated(. , fromLast = TRUE)) %>%
  select(dupl)

# check for duplicates - indicating matching predictions - identity only
dd$found_an = dd %>%
  select(-source, -head_visible, -location, -dupl, -cam_match) %>%
  mutate(found_an = duplicated(.) | duplicated(. , fromLast = TRUE)) %>%
  select(found_an)

# check for duplicates - indicating matching predictions - location only
dd$found_loc = dd %>%
  select(-source, -head_visible, -animal_id, -dupl, -found_an, -cam_match) %>%
  mutate(found_loc = duplicated(.) | duplicated(. , fromLast = TRUE)) %>%
  select(found_loc)



# see which predicitons of pipeline were matched
ddd = dd %>% filter(dd$animal_id %in% c(1,2)) %>%
  filter(source == "location")

length(unique(ddd$file_name))

# number of correct predicitons and head_visibility
table(ddd$dupl$dupl, ddd$head_visible)
# mean number of correct predicitons - accuracy
mean(ddd$dupl$dupl, na.rm = TRUE)
# number of correct identifications and head_visibility
table(ddd$head_visible, ddd$found_an$found_an)
# mean number of correct identity predicitons
mean(ddd$found_an$found_an, na.rm = TRUE)
# number of correct location matches and head_visibility
table(ddd$found_loc$found_loc)
# mean number of correct location predicitons
mean(ddd$found_loc$found_loc, na.rm = TRUE)

# recode head visible into y & n
ddd1 = ddd %>%
  mutate(h_vis = case_when(
    head_visible == 1 ~ "Y",
    head_visible != 1 ~ "N"
  ))
table(ddd1$h_vis, ddd1$dupl$dupl)

# bar plot correct predictions over head_visible
ddd %>%
  mutate(correct_prediction = case_when(
    dupl$dupl == TRUE ~ "Y",
    dupl$dupl == FALSE ~ "N"
  )) %>%
  filter(!is.na(correct_prediction)) %>%
  group_by(head_visible) %>%
  reframe(tot_count = n(),
          correct_prediction = correct_prediction) %>%
  group_by(head_visible, correct_prediction) %>%
  reframe(count = n(),
            perc = count/tot_count) %>%
  distinct() %>%
  ggplot(aes(head_visible, perc, fill = correct_prediction)) +
  geom_bar(stat = "identity") +    
  theme_classic() +
  theme(legend.position = "none")



# recode correct predicitons to y & n
dddd = ddd %>%
  mutate(correct_prediction = case_when(
    dupl$dupl == TRUE ~ "Y",
    dupl$dupl == FALSE ~ "N"
  ),
  found_an = case_when(
    found_an == TRUE ~ "Y",
    found_an == FALSE ~ "N"
  ),
  found_loc = case_when(
    found_loc == TRUE ~ "Y",
    found_loc == FALSE ~ "N"
  ),
  head_visible = as.factor(head_visible)
  )

# bar plot correct predictions over head_visible with numbers
dddd %>%
  filter(!is.na(correct_prediction)) %>%
  group_by(head_visible) %>%
  reframe(tot_count = n(),
          correct_prediction = correct_prediction) %>%
  group_by(head_visible, correct_prediction) %>%
  reframe(count = n(),
          perc = count/tot_count) %>%
  distinct() %>%
  ggplot(aes(head_visible, perc, fill = correct_prediction)) +
  geom_bar_pattern(stat = "identity",
                   pattern_color = "white",
                   pattern_fill = "white",
                   aes(pattern = correct_prediction)) +
  geom_text(aes(label=round(perc, digits = 3)*100), position = position_stack(vjust = 0.5)) +
  theme_classic()

table(dddd$head_visible, dddd$correct_prediction)


# bar plot correct identity predictions over head_visible
dddd %>%
  group_by(head_visible) %>%
  reframe(tot_count = n(),
          found_an = found_an) %>%
  group_by(head_visible, found_an) %>%
  reframe(count = n(),
          perc = count/tot_count) %>%
  distinct() %>%
  ggplot(aes(head_visible, perc, fill = found_an)) +
  geom_bar_pattern(stat = "identity",
                   pattern_color = "black",
                   pattern_fill = "black",
                   aes(pattern = found_an)) +
  geom_text(aes(label=round(perc, digits = 3)*100), position = position_stack(vjust = 0.5)) +
  theme_classic()


# bar plot correct locations over head_visible
dddd %>%
  group_by(head_visible) %>%
  reframe(tot_count = n(),
          found_loc = found_loc) %>%
  group_by(head_visible, found_loc) %>%
  reframe(count = n(),
          perc = count/tot_count) %>%
  distinct() %>%
  ggplot(aes(head_visible, perc, fill = found_loc)) +
  geom_bar_pattern(stat = "identity",
                   pattern_color = "black",
                   pattern_fill = "black",
                   aes(pattern = found_loc)) +
  geom_text(aes(label=round(perc, digits = 3)*100), position = position_stack(vjust = 0.5)) +
  theme_classic()

