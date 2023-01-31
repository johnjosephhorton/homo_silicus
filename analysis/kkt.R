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

con <- dbConnect(RSQLite::SQLite(), "../data/kkt.db")

current.id <- dbGetQuery(con, "select max(experiment_id) from responses") %>% as.numeric

query <- paste0("select 
json_extract(observation, '$.choice') as choice,
json_extract(observation, '$.politics') as politics,
json_extract(observation, '$.neutral') as neutral,
json_extract(observation, '$.new_price') as new_price,
json_extract(observation, '$.model') as model,
experiment_id
from responses
where experiment_id == ", current.id) 
    
labels <- list("1" = "Completely Fair",
               "2" = "Acceptable",
               "3" = "Unfair",
               "4" = "Very Unfair")

df.raw <- dbGetQuery(con, query) %>% mutate(choice = readr::parse_number(choice)) %>%
    mutate(choice.label = as.character(labels[choice]))

df <- df.raw %>% group_by(new_price, choice.label) %>%
    summarize(num.obs = n()) %>%
    group_by(new_price) %>% 
    mutate(frac = num.obs / sum(num.obs))

ggplot(data = df, aes(x = choice.label, y = frac)) + geom_bar(stat = "identity") +
    facet_wrap(~new_price, ncol = 1)


df <- df.raw %>% group_by(new_price, choice.label, politics, neutral) %>%
    summarize(num.obs = n()) %>%
    group_by(new_price, politics, neutral) %>% 
    mutate(frac = num.obs / sum(num.obs)) %>%
    mutate(framing = factor(ifelse(neutral, "changes", "raises"))) %>%
    mutate(new_price.pretty = paste0("Price from $15/shovel to\n $", new_price, "/shovel\nafter snowstorm"))

df$new_price.pretty <- with(df, reorder(new_price.pretty, new_price, mean))

df$new.politics <- with(df,
                    factor(as.character(politics),
                           levels = 
                               c("socialist", "leftist", "liberal", 
                                 "moderate", "conservative", "liberterian")))
                    
g <- ggplot(data = df, aes(x = choice.label, y = frac, fill = factor(framing))) +
    geom_bar(stat = "identity", colour = "black") +
    facet_grid(new.politics~new_price.pretty) +
    theme_bw() +
    ylab("Count of answers") + 
    theme(strip.text.y.right = element_text(angle = 45), legend.position = "top",
          panel.grid.major = element_blank(), panel.grid.minor = element_blank()) +
    scale_fill_manual("Framed as:", values = c("Red", "Gray")) +
    geom_vline(xintercept = 1.5, colour = "gray", linetype = "dashed") +
    geom_vline(xintercept = 2.5, colour = "gray", linetype = "dashed")
    

JJHmisc::writeImage(g, "kkt", width = 11, height = 6, path = "../writeup/plots/")
