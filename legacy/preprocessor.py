# Date    : 2024/9/27 15:29
# File    : preprocessor.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


# import re
# import time
# from jionlp import recognize_location
# from jionlp import remove_email
# from jionlp import remove_phone_number
# from jionlp import remove_id_card
# from jionlp import remove_url

# def preprocess_email(content):
#     # 隐藏地址信息
#     locations = recognize_location(content)
#     for loc in locations:
#         content = content.replace(loc, '***')
    
#     # 隐藏邮箱地址
#     content = remove_email(content)
#     content = content.replace('[EMAIL]', '***')
    
#     # 隐藏电话号码
#     content = remove_phone_number(content)
#     content = content.replace('[PHONE]', '***')
    
#     # 隐藏身份证号码
#     content = remove_id_card(content)
#     content = content.replace('[ID]', '***')
    
#     # 隐藏URL
#     content = remove_url(content)
#     content = content.replace('[URL]', '***')
    
#     # 隐藏个人简介签名 (假设签名在邮件末尾,以"--"开始)
#     content = re.sub(r'--[\s\S]*$', '-- ***', content)
    
#     return content


# # 编译正则表达式
# EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
# PHONE_PATTERN = re.compile(r'\b(?:\+?86)?1[3-9]\d{9}\b')
# ID_CARD_PATTERN = re.compile(r'\b\d{17}[\dXx]\b|\b\d{15}\b')
# URL_PATTERN = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
# SIGNATURE_PATTERN = re.compile(r'--[\s\S]*$')


# def preprocess_email2(content):
#     # 使用一个字典来存储所有需要替换的内容
#     replacements = {}
    
#     # 查找所有匹配项
#     replacements.update({m.group(): '***' for m in EMAIL_PATTERN.finditer(content)})
#     replacements.update({m.group(): '***' for m in PHONE_PATTERN.finditer(content)})
#     replacements.update({m.group(): '***' for m in ID_CARD_PATTERN.finditer(content)})
#     replacements.update({m.group(): '***' for m in URL_PATTERN.finditer(content)})
    
#     # 替换签名
#     content = SIGNATURE_PATTERN.sub('-- ***', content)
    
#     # 执行所有替换
#     for old, new in replacements.items():
#         content = content.replace(old, new)
    
#     return content

# def handle_request(request):
#     email_content = request.get('email_content', '')
#     processed_content = preprocess_email2(email_content)
#     return {'processed_content': processed_content}


# if __name__ == '__main__':
#     test_content = open('testsamples/test1.txt', 'r', encoding='utf-8').read()

#     # 打印测试前长度
#     before_len = len(test_content)

#     # 打印耗时
#     start_time = time.time()
#     # 打印测试后长度
#     processed_content = preprocess_email(test_content)
#     after_len = len(processed_content)
#     open('testsamples/test1_processed1.txt', 'w', encoding='utf-8').write(processed_content)

#     # 打印耗时
#     end_time = time.time()

#     print(f"preprocess_email | 处理前长度: {before_len} | 处理后长度: {after_len} | 耗时: {end_time - start_time} 秒")

#     # 打印耗时
#     start_time = time.time()
#     # 打印测试后长度
#     processed_content = preprocess_email2(test_content)
#     after_len = len(processed_content)
#     # 保存处理后的内容
#     open('testsamples/test1_processed2.txt', 'w', encoding='utf-8').write(processed_content)
#     # 打印耗时
#     end_time = time.time()
    
#     print(f"preprocess_email2 | 处理前长度: {before_len} | 处理后长度: {after_len} | 耗时: {end_time - start_time} 秒")

import re
import time
from abc import ABC, abstractmethod
from jionlp import recognize_location, remove_email, remove_phone_number, remove_id_card, remove_url


# 抽象基类
class EmailPreprocessor(ABC):
    @abstractmethod
    def preprocess(self, content):
        pass


# JioNLP实现
class JioNLPPreprocessor(EmailPreprocessor):
    def preprocess(self, content):
        # 隐藏地址信息
        locations = recognize_location(content)
        for loc in locations:
            content = content.replace(loc, '***')
        
        # 隐藏邮箱地址
        content = remove_email(content)
        content = content.replace('[EMAIL]', '***')
        
        # 隐藏电话号码
        content = remove_phone_number(content)
        content = content.replace('[PHONE]', '***')
        
        # 隐藏身份证号码
        content = remove_id_card(content)
        content = content.replace('[ID]', '***')
        
        # 隐藏URL
        content = remove_url(content)
        content = content.replace('[URL]', '***')
        
        # 隐藏个人简介签名
        content = re.sub(r'--[\s\S]*$', '-- ***', content)
        
        return content


# 正则表达式实现
class RegexPreprocessor(EmailPreprocessor):
    def __init__(self):
        self.EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.PHONE_PATTERN = re.compile(r'\b(?:\+?86)?1[3-9]\d{9}\b')
        self.ID_CARD_PATTERN = re.compile(r'\b\d{17}[\dXx]\b|\b\d{15}\b')
        self.URL_PATTERN = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.SIGNATURE_PATTERN = re.compile(r'--[\s\S]*$')

    def preprocess(self, content):
        replacements = {}
        
        replacements.update({m.group(): '***' for m in self.EMAIL_PATTERN.finditer(content)})
        replacements.update({m.group(): '***' for m in self.PHONE_PATTERN.finditer(content)})
        replacements.update({m.group(): '***' for m in self.ID_CARD_PATTERN.finditer(content)})
        replacements.update({m.group(): '***' for m in self.URL_PATTERN.finditer(content)})
        
        content = self.SIGNATURE_PATTERN.sub('-- ***', content)
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        return content


# 预处理器工厂
class PreprocessorFactory:
    @staticmethod
    def get_preprocessor(_type):
        if _type == "jionlp":
            return JioNLPPreprocessor()
        elif _type == "regex":
            return RegexPreprocessor()
        else:
            raise ValueError("Invalid preprocessor type")

# # 使用示例
# def handle_request(request, preprocessor_type="regex"):
#     email_content = request.get('email_content', '')
#     preprocessor = PreprocessorFactory.get_preprocessor(preprocessor_type)
#     processed_content = preprocessor.preprocess(email_content)
#     return {'processed_content': processed_content}


if __name__ == '__main__':
    test_content = open('testsamples/test1.txt', 'r', encoding='utf-8').read()
    
    for preprocessor_type in ["jionlp", "regex"]:
        start_time = time.time()
        preprocessor = PreprocessorFactory.get_preprocessor(preprocessor_type)
        processed_content = preprocessor.preprocess(test_content)
        end_time = time.time()
        
        print(f"{preprocessor_type.capitalize()} Preprocessor:")
        print(f"原始长度: {len(test_content)}")
        print(f"处理后长度: {len(processed_content)}")
        print(f"耗时: {(end_time - start_time) * 1000:.2f} 毫秒\n")