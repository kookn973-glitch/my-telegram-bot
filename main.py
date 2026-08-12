import os
import requests

def download_tiktok_video(video_url):
    print("[*] جاري الاتصال بالخادم واستخراج بيانات الفيديو...")
    
    api_url = "https://tikwm.com/api/"
    params = {"url": video_url, "hd": 1}
    
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        
        if data.get("code") == 0:
            video_info = data["data"]
            download_url = video_info.get("hdplay") or video_info.get("play")
            
            if not download_url:
                print("[-] عذراً، رابط التحميل غير متوفر.")
                return

            # الحفظ في مجلد العمل الحالي لتطبيق Pydroid 3 (مضمون 100% ولا يحتاج صلاحيات معقدة)
            save_directory = os.getcwd()
            file_path = os.path.join(save_directory, "tiktok_video.mp4")
            
            print(f"[*] جاري تحميل الفيديو...")
            video_data = requests.get(download_url, stream=True)
            
            with open(file_path, "wb") as f:
                for chunk in video_data.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            # التحقق من أن الملف تم تحميله وجمه أكبر من صفر
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                print(f"[+] تم الحفظ بنجاح!")
                print(f"[+] تجد الفيديو مسجلاً في مجلد Pydroid 3 باسم:\n{file_path}")
            else:
                print("[-] حدث خطأ، الملف فارغ ولم يتم تحميله.")
                
        else:
            print("[-] فشل التحميل. تأكد من أن الرابط صحيح وعام.")
            
    except Exception as e:
        print(f"[-] حدث خطأ أثناء الاتصال: {e}")

if __name__ == "__main__":
    print("--- تحميل تيك توك (النسخة الآمنة) ---")
    url = input("أدخل رابط فيديو تيك توك هنا: ").strip()
    if url:
        download_tiktok_video(url)
    else:
        print("[-] لم تقم بإدخال أي رابط!")
