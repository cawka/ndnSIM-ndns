#!/usr/bin/env Rscript

options(gsubfn.engine = "R")
suppressPackageStartupMessages (library(sqldf))
suppressPackageStartupMessages (library(ggplot2))
suppressPackageStartupMessages (library(doBy))
suppressPackageStartupMessages (library(scales))

source ("graphs/graph-style.R")
source ("graphs/helpers.R")

input <- "results/summary-cache-att.db"
data <- sqldf("select * from data", dbname = input, stringsAsFactors=TRUE)

for(cache in c('Lru', 'Lfu', 'Random')) {
for(run in 1:5) {
x = subset(data, Run==run & Cache==cache & Size %in% c(10, 100, 1000, 10000))
x$Size = factor(x$Size,
    levels=c(10, 100, 1000, 10000),
    labels=paste('Max cache size:', c(10, 100, 1000, 10000)))

pos = read.table ('topology/7018.r0.pos.txt', header=F, col.names=c('Node','x','y'))

x2 = merge (x, pos)

## m = max(42000, max(subset(x2, Type=="CacheHits")$Packets))
m = max(subset(x2, Type=="CacheHits")$Packets)
if (m>42000) { m = round(m+500, -3) }
br = round (seq(0, sqrt(m), length.out = 5) * seq(0, sqrt(m), length.out = 5))

g = ggplot() +
    geom_point (data=x2, aes(x=-y, y=x), color='black', size=0.3) +
    geom_point (data=subset(x2, Type=="CacheHits" & Packets>0), aes(x=-y, y=x, size=Packets, color=Packets)) +
    scale_color_gradient ("Cache hits", low = "#a5daff", high = "#001088", trans = 'sqrt',
                          limits=c(1, m), breaks=br) +
    scale_size_continuous ("Cache hits", trans = 'sqrt',
                           limits=c(0, m), breaks=br) +
    theme_custom () +
    theme (axis.ticks = element_blank(),
           axis.line = element_blank (),
           axis.text = element_blank (),
           panel.grid=element_blank(),
           axis.title = element_blank ()
           ## ,
           ## panel.border = element_blank ()
           ) +
    guides( color= guide_colorbar(reverse=T) ) +
    facet_wrap (~ Size)



dir.create ("graphs/pdfs", showWarnings = FALSE, recursive = TRUE)

pdf = paste(sep='', 'graphs/pdfs/cache-hits-',cache,'-run-',run,'.pdf')
cat('Writing', pdf,'\n')

pdf (pdf, width=6.5, height=6.5)
print (g)
x = dev.off ()
} # run
} # cache

## pdf (pdf.rel, width=6.5, height=4)
## print (g.rel)
## x = dev.off ()
