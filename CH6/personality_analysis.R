library(dplyr)
library(tidyr)
library(ggplot2)
library(fmsb)
library(randomcoloR)
library(scales)

dd = read.csv("results-for-monkey_person-2023-05-30-1052.csv")

colnames(dd)

colnames(dd) = c("animal_id", "housed_with", "FN", "SN",
  "h_per_week", ">50h", "medication",
  "Fearful", "Dominant", "Persistent",
  "Cautious", "Stable", "Autistic",
  "Curious", "Thoughtless", "Stingy.Greedy",
  "Jealous", "Individualistic", "Reckless",
  "Sociable", "Distractible", "Timid",
  "Sympathetic", "Playful", "Solitary",
  "Vulnerable", "Innovative", "Active",
  "Helpful", "Bullying", "Aggressive",
  "Manipulative", "Gentle", "Affectionate",
  "Excitable", "Impulsive", "Inquisitive",
  "Submissive", "Cool", "Dependent.Follower",
  "Irritable", "Unperceptive", "Predictable",
  "Decisive", "Depressed", "Conventional",
  "Sensitive", "Defiant", "Intelligent",
  "Protective", "Quitting", "Inventive",
  "Clumsy", "Erratic", "Friendly", "Anxious",
  "Lazy", "Disorganized", "Unemotional",
  "Imitative", "Independent",
  "rater_confidence_1","rater_confidence_2","rater_confidence_3","rater_confidence_4",
  "rater_confidence_5","rater_confidence_6","rater_confidence_7","rater_confidence_8",
  "rater_confidence_9","rater_confidence_10",
  "completion_date")


unique(dd$animal_id)
dd$animal_id[which(dd$animal_id == "Malibu ")] = "Malibu"


percomponents = data.frame(dd$animal_id)
colnames(percomponents) = c("animal_id")

#Creating unit-weighted personality component scores
percomponents$Confidence= (( -dd$Fearful - dd$Submissive - dd$Timid - dd$Cautious -dd$Distractible -dd$Disorganized - dd$Dependent.Follower - dd$Vulnerable + 56 )/8)

percomponents$Openness = (( dd$Inquisitive +dd$Thoughtless + dd$Innovative + dd$Inventive + dd$Curious + dd$Imitative +dd$Impulsive)/7 )

percomponents$Dominance = ((dd$Bullying + dd$Stingy.Greedy + dd$Aggressive + dd$Irritable + dd$Manipulative + dd$Defiant + dd$Excitable 
                            + dd$Reckless + dd$Dominant + dd$Independent + dd$Individualistic - dd$Gentle + 7)/12)

percomponents$Friendliness=  ((dd$Helpful + dd$Friendly + dd$Sociable + dd$Sensitive + dd$Sympathetic + dd$Intelligent + dd$Persistent 
                               +dd$Decisive - dd$Depressed +7)/9) 

percomponents$Activity = ((dd$Active + dd$Playful -dd$Conventional - dd$Predictable - dd$Lazy -dd$Clumsy + 28 )/6 )

percomponents$Anxiety =  ((dd$Quitting + dd$Anxious + dd$Erratic + dd$Jealous  -dd$Cool - dd$Unemotional + 14)/6)

percomponents$rater = dd$FN


percomponents %>%
  filter(rater == "Emma") %>%
  filter(animal_id == "Bracken" | animal_id == "Bramble" | animal_id == "Malibu" | animal_id == "Custard") %>%
  group_by(animal_id) %>%
  summarise(across(everything(), mean)) %>%
  pivot_longer(!animal_id, names_to = "personality_trait", values_to = "score") %>%
  ggplot(., aes(personality_trait, score, fill=animal_id)) +
  geom_bar(stat="identity", position=position_dodge())



percomponents %>%
  filter(animal_id == "Malibu")




### interrater (2 animals)
library(irr)
table(dd$animal_id, dd$FN)

dd %>%
  filter(animal_id %in% c("Bracken",
                          "Bramble",
                          "Custard",
                          "Malibu")) %>%
  filter(FN %in% c("Emma", "Andrew"))

for (aid in c("Bracken",
             "Bramble",
             "Custard",
             "Malibu")){
  rnr_icc = dd %>%
  filter(animal_id == aid) %>%
  select(-c(1:2, 4:7,62:72)) %>%
  pivot_longer(!FN, names_to = "Item", values_to = "score") %>%
  pivot_wider(names_from = "FN", values_from = "score") %>%
  select(!Item) %>%
  icc(., model = "twoway", type = "agreement", unit="single")

  print(aid)
  print(rnr_icc)
}


dd %>%
  filter(animal_id == "Malibu") %>%
  select(-c(1:2, 4:7,62:72)) %>%
  filter(FN != "Emma") %>%
  pivot_longer(!FN, names_to = "Item", values_to = "score") %>%
  pivot_wider(names_from = "FN", values_from = "score") %>%
  select(!Item) %>%
  icc(., model = "twoway", type = "agreement", unit="single")

dd %>%
  filter(animal_id == "Malibu") %>%
  select(-c(1:2, 4:7,62:72)) %>%
  filter(FN != "Rachael") %>%
  pivot_longer(!FN, names_to = "Item", values_to = "score") %>%
  pivot_wider(names_from = "FN", values_from = "score") %>%
  select(!Item) %>%
  icc(., model = "twoway", type = "agreement", unit="single")

dd %>%
  filter(animal_id == "Malibu") %>%
  select(-c(1:2, 4:7,62:72)) %>%
  filter(FN != "Andrew") %>%
  pivot_longer(!FN, names_to = "Item", values_to = "score") %>%
  pivot_wider(names_from = "FN", values_from = "score") %>%
  select(!Item) %>%
  icc(., model = "twoway", type = "agreement", unit="single")


## corr interrater
library(psych)

dd %>%
  filter(animal_id == "Malibu") %>%
  select(-c(1:2, 4:7,62:72)) %>%
  pivot_longer(!FN, names_to = "Item", values_to = "score") %>%
  pivot_wider(names_from = "FN", values_from = "score") %>%
  select(!Item) %>%
  corr.test()



### cronbach alphas
library(psych)

ddr = dd %>%
  mutate(
    Fearful = 7-Fearful,
    Submissive = 7-Submissive,
    Timid = 7-Timid,
    Cautious = 7-Cautious,
    Distractible = 7-Distractible,
    Disorganized = 7-Disorganized,
    Dependent.Follower = 7-Dependent.Follower,
    Vulnerable = 7-Vulnerable,
    Gentle = 7-Gentle,
    Depressed = 7-Depressed,
    Conventional = 7-Conventional,
    Predictable = 7-Predictable,
    Lazy = 7-Lazy,
    Clumsy = 7-Clumsy,
    Cool = 7-Cool,
    Unemotional = 7-Unemotional
  )

#Confidence
ddr %>%
  filter(FN == "Emma") %>%
  select(Fearful, Submissive, Timid, Cautious, Distractible, Disorganized, Dependent.Follower, Vulnerable) %>%
  alpha(.)


#Openness
ddr %>%
  filter(FN == "Emma") %>%
  select(Inquisitive, Thoughtless, Innovative, Inventive, Curious, Imitative, Impulsive) %>%
  alpha(.)



#Dominance
ddr %>%
  filter(FN == "Emma") %>%
  select(Bullying, Stingy.Greedy, Aggressive, Irritable, Manipulative, Defiant, 
         Excitable, Reckless, Dominant, Independent, Individualistic, Gentle) %>%
  alpha(.)


#Friendliness
ddr %>%
  filter(FN == "Emma") %>%
  select(Helpful, Friendly, Sociable, Sensitive, Sympathetic, Intelligent,
         Persistent, Decisive, Depressed) %>%
  alpha(.)

#Activity
ddr %>%
  filter(FN == "Emma") %>%
  select(Active, Playful, Conventional, Predictable, Lazy, Clumsy) %>%
  alpha(.)

#Anxiety
ddr %>%
  filter(FN == "Emma") %>%
  select(Quitting, Anxious, Erratic, Jealous, Cool, Unemotional) %>%
  alpha(.)



ddr %>%
  filter(FN=="Emma") %>%
  select(-c(1:7, 62:72)) %>%
  alpha(.)




### export csv
aid_comp = percomponents %>%
  filter(rater == "Emma") %>%
  group_by(animal_id) %>%
  select(!rater) %>%
  summarise(across(everything(), mean)) %>%
  pivot_longer(!animal_id, names_to = "personality_trait", values_to = "score")

write.csv(aid_comp, "Animal_PersTraits.csv")




##Spider plot
summary_comp = percomponents %>%
  filter(rater == "Emma") %>%
  select(-rater) %>%
  # filter(animal_id %in% c("Bracken",
  #                         "Bramble",
  #                         "Brazil",
  #                         "Confetti",
  #                         "Custard",
  #                         "Malibu")) %>%
  group_by(animal_id) %>%
  summarise(across(everything(), mean))

colors = distinctColorPalette(length(summary_comp$animal_id))
transparent.colors = ggplot2::alpha(colors, alpha = 0.05)

summary_comp %>%
  select(-animal_id) %>%
  add_row(Confidence= 1,
          Openness = 1,
          Dominance = 1,
          Friendliness = 1,
          Activity = 1,
          Anxiety = 1, .before = TRUE) %>%
  add_row(Confidence=7,
          Openness = 7,
          Dominance = 7,
          Friendliness = 7,
          Activity = 7,
          Anxiety = 7, .before = TRUE) %>%
  radarchart(.,
             maxmin = TRUE,
             pcol = colors,
             pfcol = transparent.colors,
             plwd = 3,
             seg = 6
  )

legend("topright",
       legend = paste(c("B2", "B1", "B3", "C4", "C3", "C2", "C1", "M1")),
       bty = "n", pch = 20, col = colors,
       text.col = "grey25", pt.cex = 2)


for (i in c("Confidence",
            "Openness",
            "Dominance",
            "Friendliness",
            "Activity",
            "Anxiety")){
  print(apply((summary_comp[i])[1], 2,mean))
  print(apply((summary_comp[i])[1], 2,sd))
  print(range(summary_comp[i]))
}




