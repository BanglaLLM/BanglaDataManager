import time

class NewsCrawler:
    def __init__(self):
        self.data = []
        
    def get_data(self):
        return self.data
    
    def get_all_articles_of_today(self):
        pass

    def get_all_articles_of_date(self, date):
        pass

    def get_all_articles_of_month(self, month):
        pass
    
    def get_all_articles_between_dates(self, start_date, end_date):
        pass
    

def main():
    print("Data Analytics Service is running")
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()

