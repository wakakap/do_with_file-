def convert_chat_file_to_html(input_file, output_file,date,usery):
    with open(input_file, "r", encoding='utf-8') as f:
        chat = []
        message = []
        for line in f:
            line = line.strip()
            if not line:
                # 空行表示一条聊天记录结束
                if message:
                    chat.append(message)
                message = []
            else:
                # 非空行表示聊天记录中的一行
                message.append(line)
        # 将最后一条聊天记录添加到列表中
        if message:
            chat.append(message)

    html = ""
    prev_name = ""
    for message in chat:
      # 从聊天记录导出的格式 【注意看看txt里的name,datee, time的顺序，不一样对应改就行了】
      if len(message[0].split()) == 3:
          # 获取聊天记录中的姓名、时间和文本
          datee, time,name= message[0].split()
          txt = "\n".join(message[1:]).strip()
          # 处理时间格式
          hour, minute, second = time.split(':')
          hour = hour.zfill(2)
          minute = minute.zfill(2)
          second = second.zfill(2)
          time = f"{hour}:{minute}:{second}"

          # 将聊天记录转换为 HTML 格式
          if prev_name != name:
            html += f'<div class="message default clearfix" id="message1606">\n \
              <div class="pull_left userpic_wrap">\n \
                <div class="userpic userpic6" style="width: 42px; height: 42px">\n \
                  <div class="initials" style="line-height: 42px">{name[0]}</div>\n \
                </div>\n \
              </div>\n \
              <div class="body">\n \
            <div class="pull_right date details" title="{time} UTC+08:00">{time[:2]+":"+time[3:5]}</div>\n \
            <div class="from_name">{name}</div>\n'
            if txt:
              html += f' <div class="text">{txt}</div>\n'
            html += '</div> \
                    </div>\n'

          else:
            html += f'<div class="message default clearfix joined" id="message1610">\
                      <div class="body">\
                      <div class="pull_right date details" title="{time} UTC+08:00">\
                      {time[:2]+":"+time[3:5]}\
                      </div>\n'
            if txt:
                html += f' <div class="text">{txt}</div>\n'
            html += '</div> \
                    </div>\n'
          prev_name = name
      # 手动复制的格式？maybe，反正不含日期且名字在前  【处理前手动删除txt前面无关内容】
      if len(message[0].split()) == 2:
          # 获取聊天记录中的姓名、时间和文本
          name, time = message[0].split()
          txt = "\n".join(message[1:]).strip()

          # 处理时间格式
          hour, minute, second = time.split(':')
          hour = hour.zfill(2)
          minute = minute.zfill(2)
          second = second.zfill(2)
          time = f"{hour}:{minute}:{second}"

          # 将聊天记录转换为 HTML 格式
          if prev_name != name:
            html += f'<div class="message default clearfix" id="message1606">\n \
              <div class="pull_left userpic_wrap">\n \
                <div class="userpic userpic6" style="width: 42px; height: 42px">\n \
                  <div class="initials" style="line-height: 42px">{name[0]}</div>\n \
                </div>\n \
              </div>\n \
              <div class="body">\n \
            <div class="pull_right date details" title="{time} UTC+08:00">{time[:2]+":"+time[3:5]}</div>\n \
            <div class="from_name">{name}</div>\n'
            if txt:
              html += f' <div class="text">{txt}</div>\n'
            html += '</div> \
                    </div>\n'

          else:
            html += f'<div class="message default clearfix joined" id="message1610">\
                      <div class="body">\
                      <div class="pull_right date details" title="{time} UTC+08:00">\
                      {time[:2]+":"+time[3:5]}\
                      </div>\n'
            if txt:
                html += f' <div class="text">{txt}</div>\n'
            html += '</div> \
                    </div>\n'
          prev_name = name

    # 将生成的 HTML 写入输出文件

    # 顶端和底部固定的部分，需填写

    html0 = f'<!DOCTYPE html>\n \
    <html>\n \
    <head>\n \
    <meta charset="utf-8"/>\n \
    <title>Exported Data</title>\n \
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>\n \
    <link href="css/style.css" rel="stylesheet"/>\n \
    <script src="js/script.js" type="text/javascript">\n \
    </script>\n \
    </head>\n \
    \<body onload="CheckLocation();">\n \
    <div class="page_wrap">\n \
    <div class="page_header">\n \
    <div class="content">\n \
    <div class="text bold">\n \
    {usery}</div>\n \
    </div>\n \
    </div>\n \
    <div class="page_body chat_page">\n \
    <div class="history">\n \
    <div class="message service" id="message-1">\n \
    <div class="body details">\n \
    {date}\n \
    </div></div>\n'

    html0end = f'</div>\n</div>\n</div>\n</body>\n</html>\n'

    with open(output_file, "w", encoding='utf-8') as f:
        f.write(html0+html+html0end)
    


if __name__ == "__main__":

  date = "1234"# 不要求格式，自己填显示的日期
  usery = "1234"# 聊天对象
  input_file = "1234.txt"
  output_file = "1234.txt"
  convert_chat_file_to_html(input_file, output_file,date,usery)
