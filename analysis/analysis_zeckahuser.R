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

con <- dbConnect(RSQLite::SQLite(), "../data/zeckhauser.db")

## a) Allocate 70% to auto safety and 30% to highway safety. 
## b) Allocate 30% to auto safety and 70% to highway safety.
## c) Allocate 60% to auto safety and 40% to highway safety.
## d) Allocate 50% to auto safety and 50% to highway safety.

car_fraction = list("a" = 70,
                    "b" = 30,
                    "c" = 60,
                    "d" = 50)

df.raw <- dbGetQuery(con, "SELECT * FROM responses") %>%
    filter(answer != "none of the above")

# Execute a SQL query to read data from the "employees" table
df <- df.raw %>%
    mutate(car.budget = as.numeric(car_fraction[answer]))  %>%
    mutate(allocation = factor(paste0(car.budget, "% car;\n", 100 - car.budget, "% hway")),
           allocation = reorder(allocation, -car.budget, mean)
           ) %>%
    mutate(chose.status.quo = I(answer == status_quo))


m <- lm(chose.status.quo ~ scenario_name + temperature, data = df)

m.a <- felm(I(answer == "a") ~ as.numeric(I(status_quo == "a")) | factor(score) + temperature  | 0 |0, data = df)
m.b <- felm(I(answer == "b") ~ as.numeric(I(status_quo == "b")) | factor(score) + temperature  | 0 |0, data = df)
m.c <- felm(I(answer == "c") ~ as.numeric(I(status_quo == "c")) | factor(score) + temperature  | 0 |0, data = df)
m.d <- felm(I(answer == "d") ~ as.numeric(I(status_quo == "d")) | factor(score) + temperature  | 0 |0, data = df)


out.file <- "../writeup/tables/status_quo_bias.tex"
file.name.no.ext <- "status_quo_bias"
sink("/dev/null")
s <- stargazer(m.a, m.b, m.c, m.d, 
               title = "Effects of the employer prior experience",
               dep.var.labels.include = TRUE, 
               label = paste0("tab:", file.name.no.ext),
               no.space = TRUE,
               align = TRUE, 
               font.size = "small",
               star.cutoffs = NA, 
               omit.stat = c("aic", "f", "adj.rsq", "ll", "bic", "ser"),
               type = "latex"
               )
sink()

note <- c("\\\\",
          "\\begin{minipage}{0.95 \\textwidth}", 
"{\\footnotesize \\emph{Notes}: The outcome in Columns (1) and (2) are whether the employer hired anyone at all.
In Columns~(3) and (4), it is the cumulative prior earnings of the hired worker, if any.
In addition to the treatment cell indicators, one of the regressors is a whether the employer had any on-platform experience (as measured by having hired in the past).}", "\\end{minipage}")

JJHmisc::AddTableNote(s, out.file, note = note)

df.summary <- df %>% filter(scenario_name == "neutral") %>%
    group_by(score, allocation, model) %>%
    summarise(num = n(),
              status_quo = ifelse(answer == status_quo, 1, 0))

g <- ggplot(data = df.summary, aes(x = allocation, y = num)) +
    geom_bar(stat = "identity") +
    facet_grid(score ~ model) +
    theme_bw()

JJHmisc::writeImage(g, "neutral_choices", width = 7, height = 5, path = "../writeup/plots/")

df.summary <- df %>% group_by(score, allocation) %>%
    summarise(num = n())


ggplot(data = df.summary, aes(x = allocation, y = num)) + geom_bar(stat = "identity") +
    facet_wrap(~score, ncol = 1) + theme_bw()

df.summary <- df %>% group_by(score, allocation, scenario_name) %>%
    summarise(num = n(),
              status_quo = ifelse(answer == status_quo, 1, 0))

g <- ggplot(data = df.summary, aes(x = allocation, y = num, fill = factor(status_quo))) +
    geom_bar(stat = "identity") +
    facet_grid(scenario_name ~score) +
    theme_bw()  + 
    theme(legend.position = "top", axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))
    

JJHmisc::writeImage(g, "score_distro", width = 11, height = 8, path = "../writeup/plots/")


g <- ggplot(data = df, aes(x = bid, delta, colour = name)) +
    geom_text(aes(label = salary))+ 
    geom_point() +
    geom_line(aes(group = name)) + 
    facet_wrap(~title, ncol = 1) +
    scale_y_continuous(labels = scales::percent) +
    theme_bw()+
   scale_x_continuous(labels=scales::dollar_format())



