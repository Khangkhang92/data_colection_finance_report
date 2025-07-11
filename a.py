from datetime import datetime

# === Dữ liệu nền ===
can_list = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']

can_to_element = {
    'Giáp': 'Mộc', 'Ất': 'Mộc',
    'Bính': 'Hỏa', 'Đinh': 'Hỏa',
    'Mậu': 'Thổ', 'Kỷ': 'Thổ',
    'Canh': 'Kim', 'Tân': 'Kim',
    'Nhâm': 'Thủy', 'Quý': 'Thủy'
}

can_to_yinyang = {
    'Giáp': 'Dương', 'Ất': 'Âm',
    'Bính': 'Dương', 'Đinh': 'Âm',
    'Mậu': 'Dương', 'Kỷ': 'Âm',
    'Canh': 'Dương', 'Tân': 'Âm',
    'Nhâm': 'Dương', 'Quý': 'Âm'
}

element_to_organ = {
    'Mộc': 'Can - Đởm',
    'Hỏa': 'Tâm - Tiểu Trường',
    'Thổ': 'Tỳ - Vị',
    'Kim': 'Phế - Đại Trường',
    'Thủy': 'Thận - Bàng Quang'
}

element_to_disease = {
    'Mộc': 'Gan, mắt, tức ngực, đau mạn sườn',
    'Hỏa': 'Tim đập nhanh, lo âu, mất ngủ',
    'Thổ': 'Tiêu hóa kém, đầy bụng, tiêu chảy',
    'Kim': 'Ho, viêm phổi, táo bón, da khô',
    'Thủy': 'Lạnh tay chân, đau lưng, yếu sinh lý'
}

def relation(e1, e2):
    sinh = {'Mộc': 'Hỏa', 'Hỏa': 'Thổ', 'Thổ': 'Kim', 'Kim': 'Thủy', 'Thủy': 'Mộc'}
    khac = {'Mộc': 'Thổ', 'Thổ': 'Thủy', 'Thủy': 'Hỏa', 'Hỏa': 'Kim', 'Kim': 'Mộc'}

    if sinh[e1] == e2:
        return 'Sinh'
    elif khac[e1] == e2:
        return 'Khắc'
    elif sinh[e2] == e1:
        return 'Bị sinh (được trợ lực)'
    elif khac[e2] == e1:
        return 'Bị khắc (bị hao tổn)'
    else:
        return 'Không sinh/khắc trực tiếp'

def get_can(year):
    return can_list[(year - 4) % 10]

def get_season_info(month):
    if 3 <= month <= 4:
        return 'Xuân', 'Mộc'
    elif 5 <= month <= 6:
        return 'Hạ', 'Hỏa'
    elif 7 <= month <= 8:
        return 'Trưởng Hạ', 'Thổ'
    elif 9 <= month <= 10:
        return 'Thu', 'Kim'
    else:
        return 'Đông', 'Thủy'

def analyze(birth_year):
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    birth_can = get_can(birth_year)
    birth_element = can_to_element[birth_can]
    birth_organ = element_to_organ[birth_element]

    year_can = get_can(current_year)
    year_element = can_to_element[year_can]
    year_organ = element_to_organ[year_element]

    season_name, season_element = get_season_info(current_month)
    season_organ = element_to_organ[season_element]

    rel_year = relation(birth_element, year_element)
    rel_season = relation(birth_element, season_element)

    print(f"🧍‍♂️ Bản mệnh: {birth_year} ({birth_can}) → {birth_element} → {birth_organ}")
    print(f"📅 Năm hiện tại: {current_year} ({year_can}) → {year_element} → {year_organ}")
    print(f"🌤️ Mùa hiện tại: {season_name} → {season_element} → {season_organ}")
    print(f"🔁 Quan hệ bản mệnh → năm: {rel_year}")
    print(f"🔁 Quan hệ bản mệnh → mùa: {rel_season}")
    
    print("\n🔍 Nhận định bệnh lý:")
    if 'Khắc' in rel_year or 'Khắc' in rel_season:
        print(f"⚠️ Có xung khắc → dễ rối loạn:")
        print(f"• Tạng bản mệnh ({birth_organ}) → {element_to_disease[birth_element]}")
        if 'Khắc' in rel_year:
            print(f"• Tạng năm nay ({year_organ}) → {element_to_disease[year_element]}")
        if 'Khắc' in rel_season:
            print(f"• Tạng mùa ({season_organ}) → {element_to_disease[season_element]}")
    else:
        print("✅ Không có xung khắc mạnh → ít nguy cơ lệch khí, tạng ổn định.")

# 👉 Gọi thử
analyze(1960)

