import whisper
import argparse
import os
from pydub import AudioSegment

parser = argparse.ArgumentParser(description="vocal_path")
parser.add_argument("--vocal_path", type=str, help="纯人声wav所在路径,包含文件名")
args = parser.parse_args()

# asr
def asr_from_wav(vocal_path):
	model = whisper.load_model("large-v3")

	result = model.transcribe(vocal_path)
	segments = []

	segment_path = '/root/autodl-tmp/Segments/'

	# 音频文件加载
	audio = AudioSegment.from_wav(vocal_path)

	for i, sentence in enumerate(result['segments']):
		start_ms = int(sentence['start'] * 1000)  # 转换为毫秒
		end_ms = int(sentence['end'] * 1000)     # 转换为毫秒
		dur_ms = end_ms - start_ms
		text = sentence['text']

		# 计算持续时间并保留一位小数
		dur = round(dur_ms / 1000.0, 1)
		start = round(start_ms / 1000.0, 1)
		end = round(end_ms / 1000.0, 1)

		# 添加到段落列表中
		segments.append({'start': start, 'end': end, 'dur': dur, 'text': text})

		# 切割并保存音频段
		segment_audio = audio[start_ms:end_ms]
		segment_wav = os.path.join(segment_path, f'{i}.wav')
		segment_audio.export(segment_wav, format="wav")

	# 生成文件
	with open(f"{segment_path}/segments_info.txt", "w") as file:
		for i, seg in enumerate(segments):
			file.write(f"{segment_path}{i}.wav|{seg['start']}|{seg['end']}|{seg['dur']}|{seg['text']}\n")


if __name__ == '__main__':
	asr_from_wav(args.vocal_path)