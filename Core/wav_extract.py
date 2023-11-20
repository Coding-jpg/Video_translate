from moviepy.editor import VideoFileClip
import argparse
import os

# 创建解析器
parser = argparse.ArgumentParser(description="Video path")

# 添加参数
parser.add_argument("--video_path", help="视频所在路径，不包含文件名")

# 解析命令行参数
args = parser.parse_args()

def wav_extract(video_path):

	video_file = os.path.join(video_path, 'video.mp4')
	
	video = VideoFileClip(video_file)
	
	audio = video.audio
	
	wav_file = os.path.join(video_path, 'audio.wav')

	audio.write_audiofile(wav_file)
	
	video.close()

	return True

if __name__ == '__main__':
	wav_extract(args.video_path)