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
library(mlogit)
library(dfidx)
library(dplyr)

con <- dbConnect(RSQLite::SQLite(), "../data/horton.db")

current.id <- dbGetQuery(con, "select max(experiment_id) from responses") %>% as.numeric

query <- paste0("select
json_extract(observation, '$.scenario.job_json.role') as role,
json_extract(observation, '$.scenario.job_json.budget_language') as budget_language,
json_extract(observation, '$.scenario.applications_json[0]') as person_1,
json_extract(observation, '$.scenario.applications_json[0].wage_ask') as person_1_wage_ask,
json_extract(observation, '$.scenario.applications_json[0].experience') as person_1_experience,
json_extract(observation, '$.scenario.applications_json[0].education') as person_1_education,
json_extract(observation, '$.scenario.applications_json[1].wage_ask') as person_2_wage_ask,
json_extract(observation, '$.scenario.applications_json[1].experience') as person_2_experience,
json_extract(observation, '$.scenario.applications_json[1].education') as person_2_education,
json_extract(observation, '$.scenario.applications_json[1]') as person_2,
json_extract(observation, '$.decision.hired_person') as hired_person,
json_extract(observation, '$.scenario.prompt') as prompt,
json_extract(observation, '$.scenario.pair_index') as pair_index,
json_extract(observation, '$.scenario.min_wage') as min_wage, 
experiment_id
from responses
where experiment_id == ", current.id)

df.raw <- dbGetQuery(con, query) %>%
    mutate(hired.index = readr::parse_number(as.character(hired_person))) %>%
    mutate(w = ifelse(hired.index == 1, person_1_wage_ask, person_2_wage_ask)) %>%
    mutate(exper = ifelse(hired.index == 1, person_1_experience, person_2_experience)) %>%
    mutate(educ = ifelse(hired.index == 1, person_1_education, person_2_education)) %>%
    filter(hired.index == 1 | hired.index == 2)

df.raw$job_id <- 1:nrow(df.raw)

m.wage <- lm(w ~ I(min_wage > 0), data = df.raw)
m.exper <- lm(exper ~ I(min_wage > 0), data = df.raw)

stargazer::stargazer(m.wage, m.exper, type = "text")

out.file <- "../writeup/tables/horton.tex"
file.name.no.ext <- "horton"
sink("/dev/null")
s <- stargazer(m.wage, m.exper,
               column.labels = c("Hired worker wage", "Hired worker experience"), 
               title = "Effects of minimum wage on observed wage and hired worker attributes",
               #dep.var.caption = "",
               #dep.var.labels = c("Status Quo"), 
               dep.var.labels.include = TRUE, 
               label = paste0("tab:", file.name.no.ext),
               no.space = TRUE,
               align = TRUE, 
               font.size = "small",
               star.cutoffs = c(0.1, 0.05, 0.01),
               covariate.labels = c("\\$15/hour Minimum wage imposed"),
               omit.stat = c("aic", "f", "adj.rsq", "ll", "bic", "ser"),
               type = "latex"
               )
sink()

note <- c("\\\\",
          "\\begin{minipage}{0.95 \\textwidth}", 
"{\\footnotesize \\emph{Notes}: This reports the results of imposing a minimum wage on the (1) hired worker wage and (b) hired worker experience. 
}", "\\end{minipage}")
JJHmisc::AddTableNote(s, out.file, note = note)

df.person.1 <- df.raw %>%
    mutate(wage = person_1_wage_ask,
           higher.wage = person_1_wage_ask > person_2_wage_ask,
           same.wage = person_1_wage_ask == person_2_wage_ask,
           greater.experience = person_1_experience > person_2_experience, 
           exper = person_1_experience,
           educ = person_1_education,
           hired = ifelse(hired.index == 1, 1, 0)) %>%
    select(wage, exper, educ, hired, min_wage, greater.experience, higher.wage, same.wage, role, job_id) %>%
    mutate(person = 1)


df.person.2 <- df.raw %>%
    mutate(wage = person_2_wage_ask,
           higher.wage = person_2_wage_ask > person_1_wage_ask,
           same.wage = person_2_wage_ask == person_1_wage_ask,
           greater.experience = person_2_experience > person_1_experience, 
           exper = person_2_experience,
           educ = person_2_education,
           hired = ifelse(hired.index == 2, 1, 0)) %>%
    select(wage, exper, educ, hired, min_wage, higher.wage, same.wage, greater.experience, role, job_id) %>%
    mutate(person = 2)

df.combo <- rbind(df.person.1, df.person.2) %>%
    group_by(job_id) %>%
    mutate(delta.w = wage[person == 1] - wage[person == 2]) %>%
    mutate(delta.exper = exper[person == 1] - exper[person == 2]) %>%
    mutate(hired.person = ifelse(hired == 1, person, ifelse(person == 1, 2, 1)))

df.combo <- rbind(df.person.1, df.person.2) %>%
    group_by(job_id) %>%
    mutate(w.z = (wage - mean(wage))) %>%
    mutate(exper.z = exper - mean(exper)) %>%
    mutate(hired.person = ifelse(hired == 1, person, ifelse(person == 1, 2, 1)))


## Comparis of experience levels of who gets hired
df.combo %>% ggplot(aes(x = exper, fill = factor(hired))) + geom_histogram(position = "dodge2")


## Comparis of experience levels of who gets hired, by minimum mwage
df.combo %>% ggplot(aes(x = exper, fill = factor(min_wage))) + geom_histogram(position = "dodge2") +
    facet_wrap(~factor(hired), ncol = 1)

g <- ggplot(data = df.combo,
            aes(x = w.z, y = exper.z, colour = factor(hired), shape = factor(hired))) +
    geom_text(aes(label = ifelse(hired, "H", "R")), position = position_jitter(width = 0.05), size = 4) + 
    facet_wrap(~factor(ifelse(min_wage == 0, "No minimum wage", "$15/hour minimum wage")), ncol = 1) + 
    theme_bw() +
    scale_shape(solid = FALSE) +
    ylab("Relative Experience (Exper - Mean(Exper))") +
    xlab("Relative Wage Ask (Wage Ask - Mean(Wage Ask))") +
    theme(legend.position = "none") +
    scale_colour_manual("Hired", values = c("Red", "Black"))

print(g)

JJHmisc::writeImage(g, "hiring_tradeoff", width = 8, height = 3, path = "../writeup/plots/")
