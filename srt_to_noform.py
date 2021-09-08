import re
# srt文件删除所有换行和非正文内容后的部分
def srtnoform(PATH):
    readfile = open(PATH, "r",encoding='utf-8')
    newfile = open(PATH+".after.txt","w",encoding='utf-8')
    for line in readfile:
        if line == '\n':
            continue
        if re.match(r'\d+\s', line, flags=0):#匹配序号行
            continue
        if re.match(r'^00:', line, flags=0):#匹配时间行
            continue
        newfile.write(line.strip('\n'))
    readfile.close()
    newfile.close()

if __name__ == '__main__':
    PATH = input("请输入文件地址：")
    srtnoform(PATH)
