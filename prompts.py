prompt_messages_greeting = { 'en' : "Hello! This bot will show you up-to-date information on cash currency buy/sell rates in the city you choose. \n" \
                            "The data is taken from the website cash.rbc.ru. Please note that the offers displayed by banks are not always final — \
                            before visiting any bank, be sure to confirm all necessary information directly with the bank.\n", 

                            'ru' : "Здравствуйте! Настоящий Бот покажет вам актуальную информацию по ценам на покупку/продажу наличной валюты в выбранном Вами городе. \n" \
                            "Данные взяты с сайта cash.rbc.ru. Просим обратить внимание, что выставляемые банками предложения не всегда являются конечными, \
                            перед поездкой в любой банк обязательно уточните всю неоходимую информацию напряму у выбранного банка. \n"}

prompt_messages_cities = { 'en' : "Choose your city:",\
                           'ru' : "Выберите город:"}

prompt_messages_currencies = { 'en' : "✅ City selected: {city}\nNow choose currency to get top-{num_of_banks} banks quotes or choose stats "\
                               "to get general stats for available currencies:",#

                               'ru' : "✅ Выбранный город: {city}\nТеперь выберите валюту, чтобы получить топ-{num_of_banks} предложений банков или выберите статистику, \
                                чтобы увидеть общую статистику по доступным валютам:"}

prompt_messages_choiced = { 'en' : "📍 You selected:\nCity: {city}\nCurrency: {currency}",\
                            'ru' : "📍 Вы выбрали:\nГород: {city}\nВалюта: {currency}" }

prompt_choose_city_first= { 'en' : "A city hasn`t been chosen. Please choose the city fitst or start from the begining using /start command.", \
                           'ru' : "Город не был выбран. Выберите сначала город или начните заново с команды /start"}

prompt_messages_show_data= { 'en' : "Last {currency} quotes in {city}: \n",\
                             'ru' : "Последние курсы {currency} в городе {city}: \n"}

prompt_messages_no_data= { 'en' : "In current time there are no available quotes in yout city.",\
                           'ru' : "В насятощще время в Вашем городе нет доступных предложений."}

prompt_get_statistics = { 'en' : "Cash Stats for all currencies",\
                          'ru' : "Cтатистика по наличным - все валюты в городе."}


prompt_messages_crypto_or_cash = { 'en' : "Choose cash or crypto",\
                          'ru' : "Выберите статистику по по чему вы хотите получить."}

cities_prompt = {
    'MOSCOW': {'en': 'Moscow', 'ru' : 'Москва'},
    'SPB': {'en': 'SPB', 'ru' : 'Санкт-Петербург'},
    }