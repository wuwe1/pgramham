# 快照：Viaweb，1998年6月

> Source: [https://paulgraham.com/vw.html](https://paulgraham.com/vw.html)

---

2012年1月

1998年6月Yahoo收购案宣布前几个小时，我给Viaweb的网站拍了一张[快照](http://ycombinator.com/viaweb)。我想以后某天回头看看可能会很有意思。

首先注意到的是页面有多小。1998年的屏幕要小得多。如果我没记错的话，我们的首页刚好能塞进当时人们常用的窗口大小里。

那时候的浏览器（IE 6还要再过3年才会出现）字体很少，而且没有抗锯齿。如果你想让页面看起来好看，就得把展示文字渲染成图片。

你可能注意到Viaweb和[Y Combinator](http://ycombinator.com)的logo有某种相似之处。我们创办YC的时候故意这样做的，算是一个内部笑话。考虑到红色圆圈是多么基本的图形，我们创办Viaweb时让我惊讶的是很少有其他公司用它做logo。后来过了一阵我才明白[为什么](zero.html)。

在[公司页面](http://www.ycombinator.com/viaweb/com.html)上你会注意到一个神秘人物叫John McArtyem。Robert Morris（又名Rtm）在[蠕虫事件](http://en.wikipedia.org/wiki/Morris_worm)之后非常抗拒公开曝光，以至于他不想让自己的名字出现在网站上。我好不容易让他同意了一个折中方案：我们可以用他的简介但不用他的名字。后来他在这一点上[放松](http://ycombinator.com/people.html)了一些。

Trevor差不多在收购完成的同时毕业了，所以在4天之内，他从一个身无分文的研究生变成了百万富翁博士。我作为新闻稿撰写者的职业生涯巅峰之作，是一篇[庆祝他毕业](http://ycombinator.com/viaweb/trevor.html)的新闻稿，配图是我在一次会议上画的他的素描。

（Trevor还以[Trevino Bagwell](http://ycombinator.com/viaweb/tlbwebdesign.html)的身份出现在我们的网页设计师目录中，商家可以从中雇人来为他们搭建店铺。我们把他塞进去当"托"，以防某个竞争对手试图在我们的网页设计师名单里灌水。我们以为他的logo会吓跑真正的客户，但并没有。）

在90年代，要获取用户你必须被杂志和报纸提到。当时不像今天有那么多在网上被发现的途径。所以我们每月付给一家[公关公司](submarine.html)16,000美元，让他们帮我们上媒体。幸运的是，记者们[喜欢我们](http://ycombinator.com/viaweb/presquot.html)。

在我们[关于如何从搜索引擎获取流量的建议](http://ycombinator.com/viaweb/se.html)中（我觉得当时SEO这个词还没有被发明出来），我们说只有7个搜索引擎是重要的：Yahoo、AltaVista、Excite、WebCrawler、InfoSeek、Lycos和HotBot。有没有发现少了什么？Google是那年9月才成立的。

我们通过一家叫[Cybercash](http://en.wikipedia.org/wiki/CyberCash,_Inc.)的公司支持在线交易，因为如果缺少这个功能，我们在产品对比中会被打得很惨。但Cybercash太烂了，而且大多数店铺的订单量很低，商家把订单当电话订单来处理反而更好。我们网站上有一个页面专门[劝说商家不要做实时授权](http://www.ycombinator.com/viaweb/cybercash.html)。

整个网站被组织成一个漏斗，把人们引导到[试用页面](http://ycombinator.com/viaweb/tesdriv.html)。在网上试用软件在当时是一件新鲜事。我们在动态URL里放了cgi-bin来迷惑竞争对手，让他们搞不清我们的软件是怎么工作的。

我们有一些[知名用户](http://ycombinator.com/viaweb/us.html)。不用说，Frederick's of Hollywood的流量最大。我们对大型店铺收取每月300美元的固定费用，所以有流量很大的用户让人有些担忧。我曾经算过Frederick's在带宽上花了我们多少钱，大约是每月300美元。

由于我们托管了所有的店铺，这些店铺在1998年6月总共每月刚刚超过1000万次页面浏览，我们消耗了在当时看来很大的带宽。我们的办公室接了2条T1线路（3 Mb/秒）。那个年代没有AWS。即使是把服务器托管到机房，考虑到服务器出问题的频率，似乎风险也太大了。所以我们把服务器放在办公室里。更准确地说，放在Trevor的办公室里。作为独享办公室、不和其他人类共处的特殊待遇的交换条件，他不得不和6台尖叫着运转的塔式服务器共处一室。他的办公室被戏称为"热水浴缸"，因为服务器散发的热量实在太大了。大多数时候，他那一摞窗式空调还能勉强撑住。

在页面描述方面，我们有一种叫[RTML](http://ycombinator.com/viaweb/rtml.html)的模板语言，据说是某个缩写，但实际上是我用Rtm的名字命名的。RTML本质上是Common Lisp加上一些宏和库，外面套了一个结构编辑器，让它看起来像是有语法的样子。

由于我们采用持续发布，我们的软件实际上没有版本号。但那个年代行业媒体期望看到版本号，所以我们就编一个。如果我们想引起大量关注，就把版本号[设为整数](http://www.ycombinator.com/viaweb/rel4.html)。顺便说一下，那个"version 4.0"图标是用我们自己的按钮生成器做的。整个Viaweb网站都是用我们自己的软件搭建的，虽然它并不是一个在线商店，因为我们想亲身体验用户的感受。

1997年底，我们发布了一个通用的购物搜索引擎叫[Shopfind](http://ycombinator.com/viaweb/shoprel.html)。在当时来说相当先进。它有一个可编程的爬虫，能够爬取网上大部分不同的在线商店，并从中挑选出商品。
