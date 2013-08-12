#!/usr/bin/env Rscript

## options(gsubfn.engine = "R")
## suppressPackageStartupMessages (library(sqldf))
suppressPackageStartupMessages (library(ggplot2))
## suppressPackageStartupMessages (library(reshape2))
suppressPackageStartupMessages (library(doBy))

source ("graphs/graph-style.R")

run = 4
folder = 'att'

name = paste (sep="", "results/", folder, "/packets-", "run-", run, ".txt")
data = read.table (name, header=TRUE,
    ## Time	Node	FaceId	FaceDescr	Type	Packets	Kilobytes	PacketRaw	KilobytesRaw
    colClasses = c('numeric', 'factor', 'factor', 'factor', 'factor', 'numeric', 'numeric', 'numeric', 'numeric'))

data.x = subset(data, Type %in% c('InInterests', 'OutInterests') & PacketRaw>0,
    select=c(Time,Node,FaceDescr,Type,PacketRaw))

names(data.x)[names(data.x)=="PacketRaw"] <- "Requests"
data.z= summaryBy(Requests ~ Node + FaceDescr + Type, data.x, FUN=sum, keep.names=TRUE)

api.dig = subset(data.z, Type == 'InInterests' & substr(Node, 1, 4) == 'leaf' & substr(FaceDescr, 1, 11) == 'dev=ApiFace')
api.ns = subset(data.z, Type == 'OutInterests' & substr(Node, 1, 2) == 'bb' & substr(FaceDescr, 1, 11) == 'dev=ApiFace')

net.dig = subset(data.z, Type == 'OutInterests' & substr(Node, 1, 4) == 'leaf' & substr(FaceDescr, 1, 11) != 'dev=ApiFace')
net.ns  = subset(data.z, Type == 'InInterests' & substr(Node, 1, 2) == 'bb'  & substr(FaceDescr, 1, 11) != 'dev=ApiFace')

levels = c("Generated Requests", "Forwarded Requests")
api.dig = summaryBy (Requests ~ Node, api.dig, FUN=sum, keep.names=TRUE)
api.dig$Type = factor (levels[1], levels=levels)

net.dig = summaryBy (Requests ~ Node, net.dig, FUN=sum, keep.names=TRUE)
net.dig$Type = factor (levels[2], levels=levels)


levels = c("Received Requests", "Processed Requests")

net.ns  = summaryBy (Requests ~ Node, net.ns,  FUN=sum, keep.names=TRUE)
net.ns$Type = factor (levels[1], levels=levels)

api.ns  = summaryBy (Requests ~ Node, api.ns,  FUN=sum, keep.names=TRUE)
api.ns$Type = factor (levels[2], levels=levels)

dig = rbind (api.dig, net.dig)
ns  = rbind (net.ns, api.ns)
## dig = merge (api.dig, net.dig)
## ns = merge (net.ns, api.ns)

g.ns = ggplot(ns, aes(x=Node, y=Requests, color=Type, fill=Type))
g.ns = g.ns + geom_bar(position='dodge', stat='identity')
g.ns = g.ns + theme_custom ()

## print (g.ns)
## gglot

g.dig = ggplot(dig, aes(x=Node, y=Requests, color=Type, fill=Type))
g.dig = g.dig + geom_bar(position='dodge', stat='identity')
g.dig = g.dig + theme_custom ()

g.dig = ggplot(dig, aes(x=Requests, color=Type, fill=Type))
g.dig = g.dig + geom_histogram(position='dodge')
g.dig = g.dig + theme_custom ()


## print (g.dig)

dir.create (paste(sep="", "graphs/pdfs/", folder, "/"), showWarnings = FALSE, recursive = TRUE)

graphfile = paste(sep="","graphs/pdfs/", folder, "/", "run-",run,"-ns",".pdf")
pdf (graphfile)
print (g.ns)
x = dev.off ()

graphfile = paste(sep="","graphs/pdfs/", folder, "/", "run-",run,"-dig",".pdf")
pdf (graphfile)
print (g.dig)
x = dev.off ()

## graphfile = paste(sep="","graphs/pdfs/", folder, "/", name,".pdf")

## cat ("Writing to", graphfile, "\n")
## pdf (graphfile, width=10, height=7.5)


## for (run in strsplit(runs,",")[[1]]) {  
##   grid.newpage()
##   filename <- paste (sep="", "results/", folder, "/", name, "-run-", run)
##   cat ("Reading from", filename, "\n")

##   input <- paste (sep="", filename, ".db")
##   data.allFaces <- sqldf("select * from data", dbname = input, stringsAsFactors=TRUE)
  
##   ## data$Node <- factor(data$Node)
##   ## data$FaceId <- factor(data$FaceId)
##   data.allFaces$Kilobits <- data.allFaces$Kilobytes * 8
  
##   ## data.allFaces = summaryBy (. ~ Time + Node + Type, data=data, FUN=sum)

##   xmin = min(data.allFaces$Time)
##   xmax = max(data.allFaces$Time)
  
##   graph <- function (data, variable='Kilobits', legend="none") {
##     data <- subset(data, Type %in% c("InData", "OutInterests")) 
##     g <- ggplot (data,
##                  aes(x=Time))
##     g <- g + geom_point (aes_string(y=variable, color="Type"), size=1)
##     ## g <- g + geom_point (aes(y=Packets.sum, color=Type), size=1)
##     ## g <- g + scale_y_continuous (trans="log", labels = round)
##     g <- g + scale_color_manual (values=c("darkgreen", "red"))
##     g <- g + facet_wrap (~ Node, nrow=1)
##     g <- g + ggtitle ("Bandwidths")
##     g <- g + theme_custom ()
##     g <- g + theme(legend.position=legend)
##     g <- g + scale_x_continuous (limits=c(xmin, xmax))
##     ## g <- g + coord_cartesian(ylim=c(-10,1010))
##   }
  
##   ## data.good = subset ()
##   nodes.good = c(levels(data.allFaces$Node)[ grep ("^good-", levels(data.allFaces$Node)) ])
##   nodes.good = sample (nodes.good, min(length(nodes.good), 10))
##   ## nodes.good = c("good-leaf-12923")
  
##   nodes.evil = levels(data.allFaces$Node)[ grep ("^evil-", levels(data.allFaces$Node)) ]
##   nodes.evil = sample (nodes.evil, min(length(nodes.evil), 10))

##   nodes.producer = levels(data.allFaces$Node)[ grep ("^producer-", levels(data.allFaces$Node)) ]

##   g1 <- graph (subset (data.allFaces, Node %in% nodes.good),     "Kilobits")
##   g2 <- graph (subset (data.allFaces, Node %in% nodes.evil),     "Kilobits")
##   g3 <- graph (subset (data.allFaces, Node %in% nodes.producer), "Kilobits")
  
##   pushViewport(vpList(
##     viewport(x = 0.5, y = .66, width = 1, height = .33,
##       just = c("center", "bottom"), name = "p1"),
##     viewport(x = 0.5, y = .33, width = 1, height = .33,
##       just = c("center", "bottom"), name = "p2"),
##     viewport(x = 0.5, y = .00, width = 1, height = .33,
##       just = c("center", "bottom"), name = "p3")
##     ))
  
##   ## Add the plots from ggplot2
##   upViewport()
##   downViewport("p1")
##   print(g1, newpage = FALSE)
  
##   upViewport()
##   downViewport("p2")
##   print(g2, newpage = FALSE)
  
##   upViewport()
##   downViewport("p3")
##   print(g3, newpage = FALSE)
  
##   grid.newpage()
  
##   g1 <- graph (subset (data.allFaces, Node %in% nodes.good),     "Packets")
##   g2 <- graph (subset (data.allFaces, Node %in% nodes.evil),     "Packets")
##   g3 <- graph (subset (data.allFaces, Node %in% nodes.producer), "Packets")
    
##   pushViewport(vpList(
##     viewport(x = 0.5, y = .66, width = 1, height = .33,
##       just = c("center", "bottom"), name = "p1"),
##     viewport(x = 0.5, y = .33, width = 1, height = .33,
##       just = c("center", "bottom"), name = "p2"),
##     viewport(x = 0.5, y = .00, width = 1, height = .33,
##       just = c("center", "bottom"), name = "p3")
##     ))
  
##   ## Add the plots from ggplot2
##   upViewport()
##   downViewport("p1")
##   print(g1, newpage = FALSE)
  
##   upViewport()
##   downViewport("p2")
##   print(g2, newpage = FALSE)
  
##   upViewport()
##   downViewport("p3")
##   print(g3, newpage = FALSE)  
## }

## x = dev.off ()
## cat ("Done\n")
