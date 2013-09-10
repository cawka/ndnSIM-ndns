#!/usr/bin/env Rscript

options(gsubfn.engine = "R")
suppressPackageStartupMessages (library(sqldf))
suppressPackageStartupMessages (library(ggplot2))
suppressPackageStartupMessages (library(doBy))
suppressPackageStartupMessages (library(scales))

source ("graphs/graph-style.R")
source ("graphs/helpers.R")

input <- "results/summary-att.db"
data <- sqldf("select * from data", dbname = input, stringsAsFactors=TRUE)

api.dig = subset(data, Type == 'InInterests' & substr(Node, 1, 4) == 'leaf' & substr(Face, 1, 11) == 'dev=ApiFace')
api.ns = subset(data, Type == 'OutInterests' & substr(Node, 1, 2) == 'bb' &   substr(Face, 1, 11) == 'dev=ApiFace')



dig = summaryBy (Packets ~ Run + Cache + Size, api.dig, FUN=sum, keep.names=TRUE)
names(dig)[4] = "SentQueries"

ns  = summaryBy (Packets ~ Run + Cache + Size, api.ns,  FUN=sum, keep.names=TRUE)
names(ns)[4] = "ReceivedQueries"


## dig.and.ns         = rbind (dig, ns)
## dig.and.ns.summary = summarySE(dig.and.ns,"Packets",c("Cache", "Size", "Type"))

ns.summary = summarySE(ns,"ReceivedQueries",c("Cache", "Size"))
ns.summary$Cache = factor(ns.summary$Cache, levels=c("Lru", "Lfu", "Random"), labels=c("LRU", "LFU", "Random"), ordered=TRUE)

dig.and.ns = merge (dig, ns)
dig.and.ns$Ratio = dig.and.ns$ReceivedQueries / dig.and.ns$SentQueries
dig.and.ns.summary = summarySE(dig.and.ns, "Ratio", c("Cache", "Size"))
dig.and.ns.summary$Cache = factor(dig.and.ns.summary$Cache, levels=c("Lru", "Lfu", "Random"), labels=c("LRU", "LFU", "Random"), ordered=TRUE)


g.abs = ggplot(ns.summary, aes(x=Size, y=ReceivedQueries, fill=Cache)) +
    geom_bar(position=position_dodge(0.6), stat='identity', color = I('black'), width=0.6, size=0.2) +
    geom_errorbar(aes(ymin=ReceivedQueries-ci, ymax=ReceivedQueries+ci),
                  width=.2,
                  position=position_dodge(0.6),
                  color = I('black')) +
    scale_fill_brewer ("Cache type", palette = "PuOr") +
    scale_y_continuous(labels = comma_format()) +
    ## scale_x_discrete(labels = paste(sep='', levels(ns.summary$Size), '\n(', round(as.numeric(levels(ns.summary$Size))/783595 * 100, 1), '%)')) +
    xlab ("Maximum cache size, packets (cache size vs. query volume, %)") +
    ylab ("Number of received queries by authoritative name servers") + 
    ## scale_color (legend = F) +
    theme_custom ()




g.rel = ggplot(dig.and.ns.summary, aes(x=Size, y=1-Ratio, fill=Cache)) +
    geom_bar(position=position_dodge(0.6), stat='identity', color = I('black'), width=0.6, size=0.2) +
    geom_errorbar(aes(ymin=1-(Ratio-ci), ymax=1-(Ratio+ci)),
                  width=.2,
                  position=position_dodge(0.6),
                  color = I('black')) +
    scale_fill_brewer ("Cache type", palette = "PuOr") +
    scale_y_continuous(labels = percent_format()) +
    ## scale_x_discrete(labels = paste(sep='', levels(ns.summary$Size), '\n(', round(as.numeric(levels(ns.summary$Size))/783595 * 100, 1), '%)')) +
    xlab ("Maximum cache size, packets") +
    ylab ("Percent of queries satisfied by NDN caches") + 
    theme_custom ()

dir.create ("graphs/pdfs", showWarnings = FALSE, recursive = TRUE)

pdf.abs = "graphs/pdfs/queries-abs.pdf"
pdf.rel = "graphs/pdfs/cache-performance-rel.pdf"

cat('Writing', pdf.abs,'\n')
cat('Writing', pdf.rel,'\n')

pdf (pdf.abs, width=6, height=4)
print (g.abs)
x = dev.off ()

pdf (pdf.rel, width=6, height=4)
print (g.rel)
x = dev.off ()
