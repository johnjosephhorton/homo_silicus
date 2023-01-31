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

con <- dbConnect(RSQLite::SQLite(), "../data/zeckhauser_modular.db")

current.id <- dbGetQuery(con, "select max(experiment_id) from responses") %>% as.numeric
current.id <- 14

prompt <- dbGetQuery(con, "select json_extract(observation, '$.result.prompt') from responses where experiment_id == 14 limit 1")

writeLines(as.character(prompt))

query <- paste0("select 
json_extract(observation, '$.subject.score') as score, 
json_extract(observation, '$.subject.view') as view, 
json_extract(observation, '$.scenario.options') as options, 
json_extract(observation, '$.scenario.status_quo') as status_quo,
json_extract(observation, '$.result.answer') as answer,
json_extract(observation, '$.result.preferred_auto_share') as preferred_auto_share, 
experiment_id
from responses
where experiment_id == ", current.id)


df.raw <- dbGetQuery(con, query)

df <- df.raw %>%
    group_by(view) %>%
    mutate(neutral_preferred_auto_share  = preferred_auto_share[is.na(status_quo)][1]) %>%
    ungroup %>% 
    mutate(chose.status.quo = ifelse(is.na(status_quo), 0, ifelse(preferred_auto_share == status_quo, 1, 0))) %>%
    mutate(neutral = is.na(status_quo))

m <- lm(chose.status.quo ~ neutral, data = df)

m.re <- lmer(chose.status.quo ~ neutral + (1|view), data = df)

stargazer(m, m.re, type = "text")

out.file <- "../writeup/tables/status_quo_bias.tex"
file.name.no.ext <- "status_quo_bias"
sink("/dev/null")
s <- stargazer(m, m.re,
               column.labels = c("Selected Status Quo"), 
               title = "Effects of status quo framing",
               dep.var.caption = "Selected Status Quo",
               dep.var.labels = c("Status Quo"), 
               dep.var.labels.include = TRUE, 
               label = paste0("tab:", file.name.no.ext),
               no.space = TRUE,
               align = TRUE, 
               font.size = "small",
               star.cutoffs = c(0.1, 0.05, 0.01),
               covariate.labels = c("Neutral Framing"),
               omit.stat = c("aic", "f", "adj.rsq", "ll", "bic", "ser"),
               type = "latex"
               )
sink()

note <- c("\\\\",
          "\\begin{minipage}{0.95 \\textwidth}", 
"{\\footnotesize \\emph{Notes}: }", "\\end{minipage}")

JJHmisc::AddTableNote(s, out.file, note = note)


##
df.summary <- df %>% group_by(status_quo, preferred_auto_share) %>%
    summarise(num.obs = n()) %>%
    mutate(sq.choice = ifelse(preferred_auto_share == status_quo, 1, 0)) %>% 
    mutate(pretty.status_quo = ifelse(is.na(status_quo), "Neutral framing",
                                                  paste0(status_quo, "% auto \nframed as Status Quo"))) %>%  
    mutate(choice = factor(paste0(preferred_auto_share, "% car;\n", 100-preferred_auto_share, "% hwy"))) %>%
    group_by(status_quo) %>%
    mutate(frac = num.obs / sum(num.obs)) %>%
    mutate(se = sqrt(frac * (1-frac))/sqrt(num.obs))

df.summary$choice <- with(df.summary, reorder(choice, preferred_auto_share, mean))

library(scales)

g <- ggplot(data = df.summary, aes(x = choice,
                                   y = frac,
                                   fill = factor(sq.choice)
                                   )) +
    geom_bar(stat ="identity", colour = "black") +
    geom_errorbar(aes(ymin = frac - 2*se, ymax = frac + 2*se), width = 0.1) + 
    facet_wrap(~pretty.status_quo, ncol = 5) +
    theme_bw() +
    scale_y_continuous(labels = scales::percent) +
    xlab("Choice") +
    ylab("% of subjects") +
    theme(legend.position = "top", axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
    scale_fill_manual("Status Quo Choice", values = c("White", "Red"))


JJHmisc::writeImage(g, "score_distro", width = 10, height = 4, path = "../writeup/plots/")





