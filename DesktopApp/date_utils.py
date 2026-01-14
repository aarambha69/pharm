import nepali_datetime
from datetime import datetime, date

class DateUtils:
    @staticmethod
    def get_current_bs_date_str():
        """Returns current date in YYYY-MM-DD (BS) format"""
        return nepali_datetime.date.today().strftime('%Y-%m-%d')
    
    @staticmethod
    def get_current_bs_date_full():
        """Returns current date in YYYY Month DD format (e.g. 2082 Magh 14)"""
        return nepali_datetime.date.today().strftime('%Y %B %d')

    @staticmethod
    def get_current_bs_year():
        """Returns current BS year"""
        return nepali_datetime.date.today().year

    @staticmethod
    def ad_to_bs(ad_date_str):
        """Converts YYYY-MM-DD (AD) string to YYYY-MM-DD (BS) string"""
        if not ad_date_str: return ""
        try:
            # Handle if it's already a date object or full timestamp string
            if isinstance(ad_date_str, (datetime, date)):
                dt = ad_date_str
            else:
                # Truncate time part if present
                clean_date = str(ad_date_str).split('T')[0].split(' ')[0]
                dt = datetime.strptime(clean_date, '%Y-%m-%d').date()
                
            nd = nepali_datetime.date.from_datetime_date(dt)
            return nd.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Date Conversion Error: {e}")
            return str(ad_date_str) # Fallback to original if conversion fails

    @staticmethod
    def bs_to_ad(bs_date_str):
        """Converts YYYY-MM-DD (BS) string to YYYY-MM-DD (AD) string"""
        if not bs_date_str: return ""
        try:
            parts = bs_date_str.split('-')
            if len(parts) != 3: return bs_date_str
            
            y, m, d = map(int, parts)
            nd = nepali_datetime.date(y, m, d)
            ad = nd.to_datetime_date()
            return ad.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"BS to AD Error: {e}")
            return bs_date_str

    @staticmethod
    def format_bs_date_friendly(bs_date_str):
        """Converts YYYY-MM-DD (BS) to friendly format like '14 Magh, 2082'"""
        try:
            parts = bs_date_str.split('-')
            y, m, d = map(int, parts)
            nd = nepali_datetime.date(y, m, d)
            return nd.strftime('%d %B, %Y')
        except:
            return bs_date_str
