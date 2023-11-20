#### 实验硬件（不代表最低要求）
    A5000 24G 

#### 环境准备
    实验的时候用了2个虚拟环境，导致在一键运行的脚本中需要进行切换，整的比较复杂，所以分成了两个requirements，请自行处理。
    重点：由于人声分离项目（MVSEP）以及口型对齐项目（videoRetalking）包含的模型很大，干脆就没包含这俩项目，拉取本项目后，请在Core/目录下分别拉取这2个项目。项目地址如下：
    https://github.com/ZFTurbo/MVSEP-MDX23-music-separation-model
    https://github.com/OpenTalker/video-retalking
    
    
#### 运行方法：
    把视频放到/INPUT/目录下，在/autodl-tmp/目录下不激活环境，直接运行bash ./video_translate.sh <源语言> <目标语言>, 结果在OUTPUT/里，每次运行结束后保存自己需要的文件，然后运行bash clean.sh。
