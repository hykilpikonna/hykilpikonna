---
title: Maimai 街机音游逆向！
subtitle: 从拆包到脱壳到魔改遇到的各种坑
tags: [ctf]
---

不久之前某位朋友拿到了最新最热的 maimai DX 某版本的 .app 镜像，然后和ta一起折腾了几天拆包脱壳之后终于成功启动了！在这里简单写一下解包过程和学到的事情，作为记录也作为一个教程吧，希望之后尝试解包的人不需要踩同样的坑了。

## 0x1 解压 .app 包

首先，朋友拿到的文件是一个 .app，通常在官方渠道中通过 U 盘或者网络下发给官方的街机框体，这也是所有 Sega 游戏都在用的传统格式。解压起来也已经有工具和教程。首先 .app 是使用 AES128 加密的，是一个对称密钥加密算法，然而已经有人帮忙把真正街机上的密钥复制出来了，接下来就是按教程解密啦，工具和教程都在[这个仓库](https://gitdab.com/SEGA/sega/src/branch/master/tools/Filesystem)里面。

解密之后是一个两层的 VHD 文件。第一层似乎文件元信息是坏的，大部分硬盘工具分区工具解压工具都打不开，不过试了各种方案发现在 Linux 上用 qemu-nbd 可以挂载，虽然会报错。挂载用了下面那一串指令，之后把 /mnt 里面的第二层 VHD 拷出来就可以直接用 7zip 解压了。

```sh
sudo modprobe nbd
sudo qemu-nbd -c /dev/nbd0 "outer.vhd"
sudo mount /dev/nbd0 /mnt
# /mnt 里面应该有 internal_{N}.vhd
```

下面分别是两层 VHD 的文件头和 file 信息，`conectix` 开头的是第二层，`eb5290 NTFS` 开头的是第一层（以下用旧版中二节奏举例）：

![[2023-11-30 10-04.png]]

qemu-nbd 加载了第一层之后连 fdisk 都是懵的，即使是这样乱来也能挂载上也真是好神奇：

![[2023-11-30 10-08.png]]

## 0x2 Crackproof 脱壳

解开 .app 包之后脱壳反而是最难的步骤，因为没有找到任何针对 SEGA 街机的脱壳教程（所以我才在写这篇教程！）解压好文件之后发现直接运行会闪退，为什么呢？用文件识别工具 [DIE (detect it easy)](https://github.com/horsicq/Detect-It-Easy) 检测一下发现主程序 Sinmai.exe 被一个叫 HyperTech Crackproof 的工具加密过 (aka. “Htpac”)。

![[2023-11-30 10-15.png]]

啊但是 Sinmai.exe 明明就只是一个 Unity 启动器，Unity 的话所有游戏的启动器都是一样的，让每个游戏不同的是 {Game}\_Data 里面的 dll 文件，所以我直接去下了一个[开源 GTA 圣安地列斯](https://github.com/GTA-ASM/SanAndreasUnity)然后把启动器拷出来改名成 Sinmai.exe 就可以了！

![[2023-11-30 12-23.png]]

...然后还是没法启动，怎么回事呢？用 `diec` 扫描一下目录里面的所有 exe 和 dll 发现还有四个文件是加密过的：

* amdaemon.exe
* Sinmai\_Data/Managed/Assembly-CSharp.dll
* Sinmai\_Data/Plugins/Cake.dll
* Sinmai\_Data/Plugins/amdaemon_api.dll

查了一下，首先我看到 SEGA 工具库里面有一个叫 [DecryptCrackproof](https://gitdab.com/SEGA/sega/src/branch/master/tools/Crackproof/DecryptCrackproofExe64) 的工具，感觉这个尝试起来是最简单的，所以就先用它试了一下。这个工具确实自动解出来了 amdaemon.exe，但是剩下三个 DLL 都失败了，报错说 CRC32 算法的长度 out of range of valid values。

![[2023-11-30 10-31.png]]

看着这个报错，第一眼觉得应该是这个算法实现的问题，毕竟从 stack trace 可以看出传给 CalcChecksum 的参数是 UInt32，而 CRC32 函数接收的参数是 Int32... 会不会是长度超了 Int32 的最高值呢？所以就用 DotPeek 反编译、导出项目重新编译再 Debug 饶了一大圈，然后发现并不是长度超过 Int32 最高值，而是超过了整个文件的长度... 而请求长度又是一串非常不标准的计算算出来的，看来应该是 HyperTech 他们换了加密算法，并不是改一两行就能修好的。

![[2023-11-30 12-38.png]]

接下来有点没有头绪，到处查查也没有查到有用信息，有一个 [iatrepair](https://github.com/rakisaionji/iatrepair) 仓库的脱壳思路是开一个 QEMU 有 2GB 内存的 VM 里面跑游戏，等游戏加载完之后把整个系统的内存 dump 出来再解包分析... 感觉这个方法好灵车，而且这个加密也会检测系统是不是 VM。

接下来去群里问了问，群友给我了一份街机系统上会有的 odd.sys 驱动，用 OSRLoader 加载进系统就可以启动游戏了，虽然是黑屏而且不能正常启动 amdaemon。原本以为解密代码在驱动里面，所以先用 IDA Pro 打开驱动看看能不能提取出来，但是发现似乎只有一些 hashing 的 PID 验证和字符串处理，返回一个处理过的字符串，这样看来这个驱动应该是让用户进程上传识别信息来生成真正解密密钥的工具。

![[2023-11-30 12-36.png]]

但是感觉要反汇编找到真正解密的代码再重新实现出来有点太复杂了... 还是试试直接从内存里面找吧。

下载一个 CheatEngine 用来查看内存，然后启动游戏。刚开始发现 CheatEngine 的调试器挂到 Sinmai 进程上会报错，上网查了一下说可以试试在设置的调试器选项里开 DBVM 内核驱动模式，再把 Extras 里面的用内核模式浏览内存选上，然后果然就可以挂了！

![[2023-11-30 12-45.png]]

接下来打开内存视图，先看了一遍 Memory Regions 里面标注的 DLL 名，但是似乎没有我想要找的 DLL 的样子。那怎么办呢？看看有没有只属于这个 DLL 的可识别信息吧，用 hexed.it 打开上一代别人解包好的 Assembly-CSharp.dll 发现文件末尾有一串元信息，写着 "InternalName Assembly-CSharp.dll"，每个字符中间间隔着一个 NULL \\0 字符。

![[2023-11-30 12-59.png]]

所以我在 CE 内存视图里面搜这段文字然后就找到了！正好只有一个匹配结果。然后记录一下最左边的地址，打开内存区域视图找到这个地址所属的区域，右键把整个区域存下来，然后用 hexed.it 打开把 CE 的文件头去掉（截到 DLL 文件头那里）再把文件尾补到整 32 位，保存改名成 DLL 就可以了！

![[2023-11-30 13-02.png]]

之后就只差 Cake.dll 和 amdaemon_api.dll 了，可惜这两个我用同样的方法没有解出来。amdaemon_api 在游戏里并没有加载，而 Cake 是一个包含了依赖的 dll，被拆成了很多不同的内存区域导致让它完整结合回去比较麻烦，但是这两个文件在不同版本中几乎没有改动，所以就直接拿上一个版本别人脱好壳的用了（一般会放在 segatools 文件夹里一起发出来）

## 0x3 魔改

可惜脱完 dll 壳并不是直接就能玩，还要去掉一些街机验证。因为 maimai 是一个 Unity 游戏，是用 C# 写的，而众所周知 .NET 运行时的结构和 Java 差不多都是反编译出来几乎直接是源码的，所以魔改思路就是把 Assembly-CSharp 反编译成源码，改好所有的代码报错，改掉验证然后再编译回去啦。

![[2023-11-30 13-53.png]]

...结果还在修报错的时候发现朋友已经魔改完了，所以就先用别人的啦，具体需要做哪些魔改等下次拿到最新最热数据再研究好了 qwq

## 0xF 总结

总之这是我第一次做 Windows 二进制程序脱壳，感觉有别人写好的文档和群友帮忙也没有想象的那么难（以前打 CTF 从来都不敢碰 binary 题的呜呜呜）虽然是朋友先解出来魔改完了有点扫兴，但是学到了很多脱壳技巧还是很开心的！现在就差给 [AquaDX](https://github.com/hykilpikonna/AquaDX) 加服务器支持了...（下次再写 qwq
