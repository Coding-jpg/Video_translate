# -*- coding: utf-8 -*-

# This code shows an example of text translation from English to Simplified-Chinese.
# This code runs on Python 2.7.x and Python 3.x.
# You may install `requests` to run this code: pip install requests
# Please refer to `https://api.fanyi.baidu.com/doc/21` for complete api document

import requests
import random
import json
from hashlib import md5
import os
import subprocess
import re
import argparse

parser = argparse.ArgumentParser(description="Language")
parser.add_argument("--from_lang", type=str, help="源语言")
parser.add_argument("--to_lang", type=str, help="目标语言")
parser.add_argument("--inf", type=str, help="分割信息文件的路径")
args = parser.parse_args()

# 初始化key
appid = ''
appkey = ''
xikey = ''

# 读取配置文件
with open('/root/autodl-tmp/config.txt', 'r') as file:
    lines = file.readlines()
    for line in lines:
        key, value = line.strip().split('=')
        if key == 'appid':
            appid = value
        elif key == 'appkey':
            appkey = value
        elif key == 'xikey':
            xikey = value

# For list of language codes, please refer to `https://api.fanyi.baidu.com/doc/21`
from_lang = args.from_lang
to_lang = args.to_lang

endpoint = 'http://api.fanyi.baidu.com'
path = '/api/trans/vip/translate'
url = endpoint + path

# Function to generate md5 hash
def make_md5(s, encoding='utf-8'):
	return md5(s.encode(encoding)).hexdigest()

# Function to translate text using Baidu Translate API
def translate(text, from_lang, to_lang):
	salt = random.randint(32768, 65536)
	sign = make_md5(appid + text + str(salt) + appkey)
	
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}
	payload = {
		'appid': appid,
		'q': text,
		'from': from_lang,
		'to': to_lang,
		'salt': salt,
		'sign': sign
	}
	
	response = requests.post(url, params=payload, headers=headers)
	return response.json()

"""
将字幕翻译成目标语言并写入
格式
wav|start|end|dur|text
"""
def write_trans(file_name):
	with open(file_name, 'r+', encoding='utf-8') as file:
		trans_list = []
		for index, line in enumerate(file):
			parts = line.strip().split('|')
			if len(parts) > 4:
				text_to_translate = parts[4]
				translation_result = translate(text_to_translate, from_lang, to_lang)
				parts[4] = translation_result['trans_result'][0]['dst']
	
			new_line = f"{parts[0]}|{parts[1]}|{parts[2]}|{parts[3]}|{parts[4]}\n"
			print(new_line)

			trans_list.append(new_line)
		file.seek(0)
		file.truncate(0)

		file.writelines(trans_list)
	return True

'''
input: vocals_size , path of vocals
'''
def segment_for_size(vocals_size, vocals_path):

	segments_path = '/root/autodl-tmp/INPUT/Size_segments/'

	if not os.path.exists(segments_path):
		os.makedirs(segments_path)
		print(f"Folder {segments_path} create.")
	else:
		print(f"Folder {segments_path} exists.")

	file_path = '/root/autodl-tmp/INPUT/Size_segment/vocals%03d.wav'

	cmd = [
		'ffmpeg',
		'-i', vocals_path,
		'-c', 'copy',
		'-map', '0',
		'-segment_time', '25',
		'-f', 'segment',
		file_path
	]
	subprocess.run(cmd, check=True)

	return True

'''
input: segments_inf.txt
use elevenlab clone api to create a voice id for upload vocals.
return voice_id
'''
def voice_clone(file_name, vocals_path):

	url = "https://api.elevenlabs.io/v1/voices/add"
	
	headers = {
	  "Accept": "application/json",
	  "xi-api-key": f"{xikey}"
	}
	
	data = {
		'name': f'file_name',
		'description': 'Voice description'
	}
	
	vocals_size = os.stat(vocals_path).st_size / (1024*1024)
	
	# 根据原始人声分割音频
	if vocals_size > 10:
		segment_for_size(vocals_size, vocals_path)

	# 上传训练音频
	dataset = []
	segments_dir = '/root/autodl-tmp/INPUT/Size_segment/'
	for root, dirs, seg_files in os.walk(segments_dir):
		for file in seg_files:
			if file.endswith('.wav'):
				file_dir = os.path.join(root, file)
				wav_data = ('files', (file_dir, open(file_dir, 'rb'), 'audio/mpeg'))
				dataset.append(wav_data)
	
	response = requests.post(url, headers=headers, data=data, files=dataset)
	print("Successfully clone voice!\n")

	# print(response.json())
	voice_id = response.json()['voice_id']

	return voice_id

def delete_voice(voice_id):

	url = f"https://api.elevenlabs.io/v1/voices/{voice_id}"

	headers = {
	  "Accept": "application/json",
	  "xi-api-key": f"{xikey}"
	}

	response = requests.delete(url, headers=headers)
	print(f"Successfully delete the voice {voice_id}")

	return response

"""
根据英文字幕生成语音
"""
def tts(file_name, vocals_path):
	trans_text_list = []

	VOICE_ID = voice_clone(file_name, vocals_path)

	with open(file_name, 'r') as file:
		for line in file:
			parts = line.strip().split('|')
			trans_text_list.append(parts[4])

	CHUNK_SIZE = 1024

	url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
	
	headers = {
	  "Accept": "audio/mpeg",
	  "Content-Type": "application/json",
	  "xi-api-key": f"{xikey}"
	}
	
	for index, text in enumerate(trans_text_list):	
		data = {
		  "text": text,
		  "model_id": "eleven_multilingual_v2",
		  "voice_settings": {
			"stability": 0.5,
			"similarity_boost": 0.5
		  }
		}
		response = requests.post(url, json=data, headers=headers)
		with open(f'/root/autodl-tmp/Trans_vocals/{index}_trans.mp3', 'wb') as f:
			for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
				if chunk:
					f.write(chunk)

	# 删除克隆的声音
	delete_voice(VOICE_ID)

	return True

"""
计算音频长度
"""
def get_audio_length(file_path):
	"""
	使用ffmpeg获取音频时长

	:param file_path: 音频文件的路径
	:return: 音频时长（秒）
	"""
	# 调用ffmpeg来获取音频信息
	cmd = [
		'ffprobe',
		'-v', 'error',
		'-show_entries', 'format=duration',
		'-of', 'default=noprint_wrappers=1:nokey=1',
		file_path
	]

	result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	duration = result.stdout.decode('utf-8').strip()

	# 使用正则表达式来确保输出的是时长信息
	match = re.match(r'^\d+\.\d+$', duration)
	if match:
		return round(float(duration), 1)
	else:
		raise ValueError(f"Could not parse duration from ffprobe output: {duration}")

"""
音频变速
"""

def change_speed(input_file, output_file, speed_factor, duration):
	# 如果速度系数在可接受范围内，直接变速
	if 0.75 <= speed_factor <= 2.0:
		cmd = [
			'ffmpeg',
			'-i', input_file,
			'-filter:a', f"atempo={speed_factor}",
			'-vn',
			output_file
		]
		subprocess.run(cmd, check=True)
		print("normal_speed\n")
	else:
		# 临时变速文件
		temp_speed_file = f"temp_speed_{os.path.basename(output_file)}"
		# 临时沉默文件
		temp_silence_file = f"temp_silence_{os.path.basename(output_file)}"
		# 如果速度系数小于0.75，设置减速率为0.8并计算新的时长
		if speed_factor < 0.75:
			temp_speed = 0.8
			new_duration = duration / temp_speed
			
			# 变速命令
			cmd_speed = [
				'ffmpeg',
				'-i', input_file,
				'-filter:a', f"atempo={temp_speed}",
				'-vn',
				temp_speed_file
			]
			subprocess.run(cmd_speed, check=True)
			
			# 计算需要添加的沉默音频的长度
			silence_duration = new_duration - duration
			
			# 生成沉默音频命令
			cmd_silence = [
				'ffmpeg',
				'-f', 'lavfi',
				'-i', f"anullsrc=r=44100:cl=mono",
				'-t', str(silence_duration),
				temp_silence_file
			]
			subprocess.run(cmd_silence, check=True)
			
			# 合并变速后的音频和沉默音频
			cmd_merge = [
				'ffmpeg',
				'-i', 'concat:' + temp_speed_file + '|' + temp_silence_file,
				'-c', 'copy',
				output_file
			]
			subprocess.run(cmd_merge, check=True)
			
			# 删除临时文件
			os.remove(temp_speed_file)
			os.remove(temp_silence_file)

		elif speed_factor > 2.0:
			cmd = [
			'ffmpeg',
			'-i', input_file,
			'-filter:a', f"atempo={speed_factor}",
			'-vn',
			output_file
			]
			subprocess.run(cmd, check=True)

	return True

def speed_trans(file_name, directory_path, output_dir):
	dur_list = []
	mp3_files = []

	# os.walk遍历目录
	for root, dirs, files in os.walk(directory_path):
		for file in files:
			if file.endswith('.mp3'):
				mp3_files.append(os.path.join(root, file))
	# 按文件名中的数字排序
	mp3_files.sort(key=lambda x: int(x[30:-10]))

	with open(file_name, 'r') as file:
		for line in file:
			parts = line.strip().split('|')
			# 假设目标持续时间是以秒为单位
			dur_list.append(float(parts[3]))

	# speed change
	for index, target_dur in enumerate(dur_list):
		# 获取音频文件的实际长度
		actual_dur = get_audio_length(mp3_files[index])
		# 计算速度变化因子
		speed_factor = actual_dur / target_dur

		dur_analysis = f'{actual_dur}|{target_dur}|{speed_factor}\n'
		dur_analysis_path = f"{output_dir}/dur_analysis.txt"
		with open(dur_analysis_path, 'a') as file:
			file.writelines(dur_analysis)
		
		# 根据速度系数是否在ffmpeg处理范围内决定是否需要分段变速
		output_file_name = f"{index}_adjusted.wav"
		input_file = mp3_files[index]
		output_file = os.path.join(output_dir, output_file_name)
		print(f"speed_factor: {speed_factor}")
		# 调用修改后的change_speed函数，并传入目标持续时间
		change_speed(input_file, output_file, speed_factor, target_dur)

if __name__ == '__main__':

	# Read the file and translate each line
	vocals_path = '/root/autodl-tmp/Core/MVSEP-MDX23-Colab_v2/output/audio_vocals.wav'
	trans_vocals_path = '/root/autodl-tmp/Trans_vocals/'
	speed_output_dir = '/root/autodl-tmp/Trans_speed_vocals/'
	
	write_trans(args.inf)
	tts(args.inf, vocals_path)
	speed_trans(args.inf, trans_vocals_path, speed_output_dir)



