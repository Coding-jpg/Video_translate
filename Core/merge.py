import os
import argparse
import subprocess

'''
arguments
'''
parser = argparse.ArgumentParser(description="path")
parser.add_argument("--seg_path", type=str, help="segments_info.txt的路径，包括文件名")
parser.add_argument("--bgm_path", type=str, help="audio_instrum.wav的路径，包括文件名")
parser.add_argument("--speed_path", type=str, help="变速后的音频目录，不包括文件名")
parser.add_argument("--output_merge", type=str, help="合并音频的输出路径，包括文件名")
args = parser.parse_args()

'''
params: 
1. segment_path: path of segments_info.txt 
template of segments_info.txt is like ->
wav|start|end|dur|text
2. bgm_path: path of audio_instrum.wav
3. speed_vocals_path: path of transpeed vocals

function:
merge every single translated & transpeed vocal to 
the bgm audio, which is extracted by MVSEP

return bool

'''
def merge_audio_with_bgm(segment_path, bgm_path, speed_vocals_path, output_merge):
	# 音频文件列表和它们的开始时间（毫秒）
	audio_list, start_list, vocal_list = [], [], []

	with open(segment_path, 'r') as seg_file:
		for line in seg_file:
			parts = line.strip().split('|')
			start_list.append(int(float(parts[1]) * 1000))  # 转换为毫秒并确保为整数

	for root, dirs, files in os.walk(speed_vocals_path):
		for file in files:
			if file.endswith('.wav'):
				vocal_path = os.path.join(root, file)
				vocal_list.append(vocal_path)

	for vocal, start in zip(vocal_list, start_list):
		audio_list.append((vocal, start))

	# 构建 FFmpeg 复杂过滤器字符串
	filter_complex = "[0:a]volume=0.8[a0];"  # 调整背景音乐的音量
	for i, (file, start_time) in enumerate(audio_list, start=1):
		# 为每个音频文件添加 adelay 和 apad 过滤器
		delay = start_time
		filter_complex += f"[{i}:a]adelay={delay}|{delay},apad[aud{i}];"
	
	# 添加混合所有音频流的 amix 过滤器
	mix_inputs = ''.join(f"[aud{i}]" for i in range(1, len(audio_list) + 1))
	filter_complex += f"[a0]{mix_inputs}amix=inputs={len(audio_list) + 1}:duration=first, loudnorm[a]"

	# FFmpeg 命令
	cmd = ['ffmpeg', '-i', bgm_path]  # 添加背景音乐

	# 为每个音频文件添加输入参数
	for file, _ in audio_list:
		cmd += ['-i', file]

	# 添加过滤器和输出文件配置
	cmd += [
		'-filter_complex', filter_complex,
		'-map', '[a]',
		output_merge
	]

	# 执行命令
	try:
		subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
	except subprocess.CalledProcessError as e:
		print("FFmpeg Error:", e.stderr.decode())



if __name__ == '__main__':
	merge_audio_with_bgm(args.seg_path, args.bgm_path, args.speed_path, args.output_merge)