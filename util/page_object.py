class Page_object:
    objects = []
    page_number = None
    current_page = None


    def __init__(self, page, page_number):
        self.objects = page.object_list
        self.page_number = page_number
        self.current_page = page.number


