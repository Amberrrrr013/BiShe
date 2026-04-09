from models.tts import WERDetector

wer = WERDetector()

# 测试标点去除
print('=== 测试标点去除 ===')
print('Strip "hello,":', wer._strip_punctuation('hello,'))
print('Strip "\"hello":', wer._strip_punctuation('"hello'))
print('Strip "world!"', wer._strip_punctuation('world!'))

# 测试分词
print('\n=== 测试分词 ===')
print('Tokenize "Hello, world!":', wer._tokenize('Hello, world! This is a test.'))

# 测试 WER
print('\n=== 测试 WER ===')
ref = 'Hello world test'
hyp = 'Hello world test'
result = wer.calculate_wer(ref, hyp)
print(f'Ref: "{ref}"')
print(f'Hyp: "{hyp}"')
print(f'WER: {result.wer:.2%}')

ref = 'Hello, world!'
hyp = 'Hello world'
result = wer.calculate_wer(ref, hyp)
print(f'\nRef: "{ref}"')
print(f'Hyp: "{hyp}"')
print(f'WER: {result.wer:.2%}')
