#!/usr/bin/env Rscript

library(DBI)
library(RSQLite)
library(lfe)
library(tidyr)
library(magrittr)
library(dplyr)
library(ggplot2)
library(scales)
library(JJHmisc)
library(stargazer)
library(jsonlite)
library(lme4)
library(scales)

con <- dbConnect(RSQLite::SQLite(), "../data/charness_rabin.db")

current.id <- dbGetQuery(con, "select max(experiment_id) from responses") %>% as.numeric

query <- paste0("select 
json_extract(observation, '$.scenario') as scenario,
json_extract(observation, '$.scenario_name') as scenario_name,
json_extract(observation, '$.choice') as choice,
json_extract(observation, '$.personality') as personality,
json_extract(observation, '$.model') as model,
experiment_id
from responses
where experiment_id == ", current.id)

charness.rabin <- c(
    "Berk29" = .31,
    "Barc2" = .52,
    "Berk23" = 1.00,
    "Barc8" = 0.67,
    "Berk15" = 0.27,
    "Berk26" = 0.78)

df.real <- data.frame(scenario_name = names(charness.rabin),
                      exp.frac = charness.rabin[names(charness.rabin)])

df.raw <- dbGetQuery(con, query) %>% left_join(df.real)

df.raw %<>% mutate(scenario.pretty.name = paste0(scenario_name, "\n", scenario)) %>%
    mutate(personality = paste0("GPT3 Endowed with:\n\"",
                                gsub("You only care about", "You only care about\n",
                                     personality), "\""))

df.exp <- df.raw %>% filter(model == "text-davinci-003") %>% group_by(scenario.pretty.name) %>%
    summarise(n.obs = n(),
              exp.frac = mean(exp.frac)
              )

df.raw %<>% mutate(model.type = ifelse(model == "text-davinci-003",
                                       "Advanced GPT3\n(davinci-003)",
                                       "Prior GPT3\n({ada, babbage, currie}-001)"))

df <- df.raw %>%
    group_by(scenario.pretty.name, choice, model.type, personality) %>%
    summarise(n.obs = n()) %>%
    group_by(personality, scenario.pretty.name, model.type) %>%
    mutate(frac = n.obs / sum(n.obs)) %>%
    select(-n.obs) 

cr.pop <- "Charness & Rabin\n Population"
df.combo <- rbind(df, df.exp %>% mutate(personality = cr.pop, frac = exp.frac, choice = "Left", model.type = "Human Brain"))

g <- ggplot(df.combo, aes(x = choice, y = scenario.pretty.name)) +
    geom_tile(aes(fill = frac), width = 0.7, height = 0.7,
              colour = "black") +
    facet_grid(model.type~personality) +
    theme_bw() + 
    theme(strip.text.y.right = element_text(angle = 0), legend.position = "none",
          panel.grid.major = element_blank(), panel.grid.minor = element_blank()) +
    geom_label(data = df.combo, aes(label = round(frac, 2))) +
    xlab("Choices") +
    ylab("") +
    geom_vline(xintercept = 1.5, colour = "gray", linetype = "dashed")


JJHmisc::writeImage(g, "charness_rabin", width = 11, height = 6, path = "../writeup/plots/")
