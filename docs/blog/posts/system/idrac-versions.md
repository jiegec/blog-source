---
layout: post
date: 2021-03-03
tags: [poweredge,dell,idrac]
categories:
    - system
---

# iDRAC 各版本

## iDRAC 版本

目前接触到的 iDRAC 版本有：7 8 9。一些常见的服务器型号和 iDRAC 版本对应关系：

- 7: PowerEdge R320, PowerEdge R720
- 8: [PowerEdge R730xd](https://www.dell.com/support/home/en-us/product-support/product/poweredge-r730xd/drivers)，PowerEdge R630，PowerEdge R730，PowerEdge C4130
- 9: [PowerEdge R7425](https://www.dell.com/support/home/en-us/product-support/product/poweredge-r7425/drivers)

基本上，如果是 PowerEdge R 什么的，就看第二位数字，就可以推断出版本号了。

下面列举了一下可能会用到的版本。

## iDRAC 7

[iDRAC 7 在 2020 年 2 月停止更新了](https://www.dell.com/support/kbdoc/en-us/000175831/support-for-integrated-dell-remote-access-controller-7-idrac7)，最新版本是 2.65.65.65。

升级路线参考：[Reddit](https://www.reddit.com/r/homelab/comments/abuc09/psa_read_this_before_you_upgrade_your_firmware_on/)。

- 1.66.65 [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=3f4wv)，2014 年 12 月版本。
- 2.10.10.10 [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverId=Y5K20)，2015 年 4 月版本。
- 2.65.65.65 [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=0ghf4)，2020 年 3 月版本，添加了 HSTS。

## iDRAC 8

- 2.10.10.10 [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=fm1pc)，2015 年 3 月版本。
- 2.30.30.30: [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=5gchc)，2016 年 2 月版本，添加了 HTML5 virtual console 支持。
- 2.60.60.60: [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=cx8n2)，2018 年 6 月版本，添加了 virtual media over HTTP 支持。
- 2.70.70.70: [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=dnh17)，2019 年 10 月版本。
- 2.75.75.75: [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=krcxx)，2020 年 6 月版本。
- 2.75.100.75: [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=dpv0r)，2021 年 1 月版本。

## iDRAC 9

- 4.00.00.00: [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=4jcpk)，2019 年 12 月版本。LLDP 连接视图。
- 4.22.00.00: [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=9f2tg)，2020 年 7 月版本。
- 4.40.00.00: [下载页面](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=62gw1)，2020 年 12 月版本，下一代的 iDRAC virtual console 和 virtual media，支持 Infiniband。
