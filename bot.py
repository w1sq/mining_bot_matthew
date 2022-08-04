from distutils.command.config import config
from distutils.fancy_getopt import wrap_text
import aiofiles
import aiogram
from config import Config
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from db.storage import UserStorage, User, PhrasesStorage, Phrase
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember
import typing
import aioschedule as schedule

class GetAnswer(StatesGroup):
    answer_paid_id = State()
    hash_link_await = State()
    phrases_file = State()
    answer_limit = State()
    answer_unpaid_id = State()
    
class TG_Bot():
    def __init__(self, user_storage: UserStorage, phrases_storage:PhrasesStorage):
        self._user_storage:UserStorage = user_storage
        self._phrases_storage:PhrasesStorage = phrases_storage
        self._bot:aiogram.Bot = aiogram.Bot(token=Config.TGBOT_API_KEY)
        self._storage:MemoryStorage = MemoryStorage()
        self._dispatcher:aiogram.Dispatcher = aiogram.Dispatcher(self._bot, storage=self._storage)
        self._disable_web_page:bool = True
        self._accounts_in_process_pool = {}
        self._create_keyboards()

    async def reset_limits(self):
        users = await self._user_storage.get_all_members()
        for user in users:
            await self._user_storage.reset_limit(user)

    async def init(self):
        schedule.every().day.at("00:00").do(self.reset_limits)
        self._init_handler()

    async def start(self):
        print('Bot has started')
        await self._dispatcher.start_polling()
    
    def _generate_menu_keyb(self, user:User):
        match user.role:
            case User.USER:
                local_keyb = ReplyKeyboardMarkup(resize_keyboard=True)\
                .row(KeyboardButton('👤 Мой ID'),KeyboardButton('✒️ Обучение'))\
                    .row(KeyboardButton('❓️ Вопрос-ответ'), KeyboardButton('✉️ Поддержка'))\
                        .row(KeyboardButton("✅ Купить программу"))
            case User.ADMIN:
                local_keyb = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('👤 Мой ID'),KeyboardButton('✒️ Начать обучение'))\
                .row(KeyboardButton('✅ Докупить БД'), KeyboardButton('↕️ Админка'))\
                    .row(KeyboardButton("↙️ Скачать программу"))
            case User.PAID:
                local_keyb = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('👤 Мой ID'),KeyboardButton('✒️ Начать обучение'))\
                .row(KeyboardButton('✅ Докупить БД'), KeyboardButton('✉️ Поддержка'))\
                    .row(KeyboardButton("↙️ Скачать программу"))
        return local_keyb.row(KeyboardButton(f"✨ Генерировать фразу ({user.actual_limit})"))

    async def _show_menu(self, message:aiogram.types.Message , user:User):
        local_keyb = self._generate_menu_keyb(user)
        await message.answer('Выберите интересующий вас пункт навигации:', reply_markup=local_keyb)

    async def _will_think(self, message:aiogram.types.Message, user:User):
        local_keyb = self._generate_menu_keyb(user)
        await message.answer('😏 Конечно, мы тебя не торопим. Только помни, пока ты думаешь, кто-то уже зарабатывает.', reply_markup=local_keyb)

    async def _check_subscription(self, message:aiogram.types.Message, user:User):
        match user.role:
            case User.PAID:
                await message.answer(text='✅ Свою часть сделки вы выполнили, спасибо! Хотите начать обучение?',reply_markup=self._checked_subscription_keyboard_access)
            case _:
                await message.answer(text='✅ Свою часть сделки вы выполнили, спасибо! Хотите начать обучение?',reply_markup=self._checked_subscription_keyboard)

    async def _start_paid_education(self, message:aiogram.types.Message, user:User):
        local_keyb = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton(text='MacOS'), KeyboardButton(text='WINDOWS')).row(KeyboardButton(text="Android"), KeyboardButton(text="IOS"))
        await message.answer("💌 Я очень рад, что ты приобрёл мой продукт. Я уверен - он тебя не разочарует.\n\nПришло время автоматизировать процесс поиска забытых кошельков. Давай я тебя всему научу, а тебе останется только ждать своей первой прибыли.\n\nМы предоставляем полную поддержку в течение 24 часов, в которые ты всегда можешь написать мне свой вопрос или попросить помощи.\n\n💸💸💸💸💸", reply_markup=local_keyb)

    async def _step1_paid_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("⤵️ Я скачал и установил Python"))
        links_keyb = InlineKeyboardMarkup().row(InlineKeyboardButton(text='Скачать Python', url='https://www.python.org/ftp/python/3.10.5/python-3.10.5-amd64.exe'))
        async with aiofiles.open('pics/python.jpg','rb') as f:
            await message.answer_photo(f, caption='Первый этап - установка Python на твой компьютер.\n\nПо ссылке ниже ты можешь скачать последнюю версию для своей ОС. Так как программа написана на этом языке - это ПО является обязательным к установке.')
        await message.answer(text='Запускаем скачанный файл и устанавливаем Python. В процессе установки отмечаем галочкой в графе path.',reply_markup=links_keyb)
        await message.answer('Всё готово? Идём дальше!', reply_markup=reply_markup)
    
    async def _step2_paid_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("⤵️ Я скачал и установил библиотеку"))
        async with aiofiles.open('pics/bit.jpg','rb') as f:
            await message.answer_photo(f, caption='Второй этап - тебе нужно установить библиотеку BIT.\n\nДля чего это нужно?\n\nОсновная задача библиотек – они несут в себе набор функций, которые решают конкретную задачу в программе. Она может применять шаблоны сообщений, ранее скомпилированный код, классы или подпрограммы — и использоваться много раз. В языках программирования есть стандартные библиотеки, но разработчик также может создать свою.', parse_mode=aiogram.types.ParseMode.MARKDOWN)
        await message.answer('🔼 Для установки открываем командную строку комбинацией `win+R`, после чего вписываем `pip install bit`.\n\nНажимаем Enter и ждём завершения установки.', reply_markup=reply_markup, parse_mode=aiogram.types.ParseMode.MARKDOWN)
    
    async def _step3_paid_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("⤵️ Я скачал программу"))
        links_keyb = InlineKeyboardMarkup().row(InlineKeyboardButton(text='Скачать программу:', url='https://clck.ru/sM9od'))
        async with aiofiles.open('pics/program.jpg','rb') as f:
            await message.answer_photo(f, caption='Скачивание программы.\n\nПо ссылке ниже ты можешь скачать готовый продукт. Его не нужно устанавливать, просто подбери для него подходящее место на диске и распакуй в него архив.')
        await message.answer(text='Скачать программу можно по ссылке:',reply_markup=links_keyb)
        await message.answer('Всё готово? Идём дальше!', reply_markup=reply_markup)
    
    async def _step4_paid_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("⤵️ Я скачал базу данных"))
        links_keyb = InlineKeyboardMarkup().row(InlineKeyboardButton(text='Скачать базу данных(100к)', url='https://clck.ru/sHDtn'))
        async with aiofiles.open('pics/wallets_base.jpg','rb') as f:
            await message.answer_photo(f, caption='Шаг четвёртый - скачивание базы данных с BTC кошельками.\n\nПо ссылке ниже тебе нужно скачать архив с txt файлом, в котором содержатся адреса 100.000 BTC кошельков.\n\nМного ли это - 100к?\n\nДаже если у вас будет 1 кошелёк, а не 100.000 - вы сможете перебирать его 2048^12 раз, в конечном счёте подобрав нужную фразу. Однако чем кошельков больше (чем больше база) - тем больше шансов получить к ним доступ.\n\nТекстовый файл с базой необходимо закинуть в ту же папку, где находится наша программа.')
        await message.answer(text='Скачать базу данных можно по ссылке:',reply_markup=links_keyb)
        await message.answer('При желании увеличить шансы поиска вы можете дополнительно приобрести нужное вам количество кошельков в свою базу. Каждые дополнительные 50.000 кошельков обойдутся вам всего в 5$.', reply_markup=reply_markup)
    
    async def _step5_paid_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("✅ Завершить обучение")).row(KeyboardButton("✉️ Поддержка"))
        await message.answer(text='Уже почти всё! Не терпится начать майнить?\n\nВсё что осталось сделать - это запустить нашу программу.',reply_markup=reply_markup)
        async with aiofiles.open('pics/execute.jpg','rb') as f:
            await message.answer_photo(f, caption='Попробуй запустить файл start.py двойным кликом.\n\nЕсли ничего не произошло, то открываем командную строку сочетанием клавиш WIN+R. После чего вставляем команду следующим образом:\n\n`python *расположение программы*`.\n\nДалее нажимаем Enter и у нас должна открыться консоль. Если всё прошло хорошо, в результате вы увидите перебор кошельков и фраз со строками: `generation` и `verification`.', parse_mode = aiogram.types.ParseMode.MARKDOWN)
        await message.answer('Обрати внимание на то, что путь программы должен совпадать с тем, что вписывается для запуска.')
    
    async def _step6_paid_education(self, message:aiogram.types.Message, user:User):
        local_keyb = self._generate_menu_keyb(user)
        await message.answer("🔥 Поздравляем, вы успешно прошли обучение майнинга.\n\nХочу ещё раз поблагодарить за то, что воспользовался моим продуктом. Если нужны будут дополнительные базы - всегда можешь докупить в боте.\n\nНе выключай уведомления.\n\nПроцесс работы программы заключается в генерации случайного ключа, получении из него адреса и проверки наличия такого адреса в базе.", reply_markup=local_keyb)

    async def _start_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("⤵️ Шаг 1"))
        await message.answer(text='Как и договаривались, я научу тебя майнить криптокошельки с балансом на своём мобильном устройстве.\n\nПоверь, это только на первый взгляд кажется сложным и непонятным, а по факту это проще, чем зарегистрироваться в одноклассниках.\n\nВнимательно следуй инструкциям.\nУ тебя всё получится  🚀',reply_markup=reply_markup)

    async def _step2_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("⤵️ Я создал кошелёк"))
        await message.answer(text='Если ты никогда не имел дело с криптовалютой, то тебе стоит пройти весь путь от А до Я. Для начала давай заведём тебе собственный холодный кошелек. Нужен он всего лишь для того, чтобы на практике понять, как работает блокчейн.\n\nПосле установки:\n\n1. Выбираете "Создать новый кошелек"\n2. Придумываете и запоминаете пин-код\n3. Ставите галочку "Я понимаю, что если я потеряю секретную фразу, я потеряю доступ к своему кошельку"\n4. Записываете секретную фразу в блокнот и подтверждаете её',reply_markup=reply_markup)
        download_links_keyboard = InlineKeyboardMarkup().row(InlineKeyboardButton(text='Play Market', url='https://play.google.com/store/apps/details?id=com.wallet.crypto.trustapp')).row(InlineKeyboardButton(text='App Store', url='https://apps.apple.com/app/apple-store/id1288339409?mt=8'))
        await message.answer(text='Ссылки для скачивания:', reply_markup=download_links_keyboard)

    async def _step3_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("✨ Сгенерировать фразу"))
        await message.answer(text='Отлично! Ты зарегистрировал свой крипто-кошелек.\n\nПри регистрации вы не указывали свои паспортные данные, номер телефона или адрес электронной почты.\nПричиной тому — анонимность и децентрализованость сетей блокчейна. Единственным доказательством того, что этот кошелек и деньги на нём ваши — секретная фраза.\n\nТут мы и подошли к сути нашего проекта: мы занимаемся тем, что генерируем такие же фразы и восстанавливаем доступ к случайным  кошелькам.\n\nДавай попробуем?',reply_markup=reply_markup)

    async def _step4_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("✅ Готово"))
        await self._user_storage.decrease_phrases(user)
        phrase = await self._phrases_storage.get_random_phrase()
        await message.answer(f"`{phrase}`", parse_mode=aiogram.types.ParseMode.MARKDOWN)
        await message.answer(text='↗️↗️↗️↗️↗️↗️↗️↗️↗️↗️\n\nЭта секретная фраза называется мнемонической или seed фразой\nОна состоит из 12 слов из словаря Bip39 (https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt) в котором находится 2048 слов.\n\nМы знаем алгоритм построения таких фраз и готовы ежедневно генерировать по 10 фраз для вас. Проверяй, что хранится на том кошельке:\n\n1. Скопируйте фразу сообщением выше\n2. Зайди в настройки приложения Trust и нажми на "Кошельки"\n3. В правом верхнем углу нажми на плюс\n4. Выбери "У меня уже есть кошелёк"\n5. Мульти-монетный кошелек\n6. Вставить и импортировать',reply_markup=reply_markup)

    async def _step5_education(self, message:aiogram.types.Message, user:User):
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("✅ Начать майнить"))
        await message.answer(text='Редко случается так, что с первого раза попадается кошелек с балансом. Твоя задача пробовать ещё и ещё до тех пор, пока что-то не найдёшь.\n\nЧтобы тебе было проще ориентироваться, держи кошелек с рабочей фразой, на которой есть баланс.\n\n`volume distance dash huge giggle vehicle solve author swallow perfect coyote useless`\n\nЭто не подарок, так что даже не пытайся вывести от туда деньги.\n\nУ тебя всё равно не получится, так как на этом кошельке монеты, которые невозможно перевести, обменять или продать.',reply_markup=reply_markup, parse_mode= aiogram.types.ParseMode.MARKDOWN)

    async def _get_support_info(self, message:aiogram.types.Message, user:User):
        local_keyb = self._generate_menu_keyb(user)
        await message.answer(text='⁉️ По всем вопросам связанным с продуктом - @petorlov\n\nПостарайтесь коротко и в одном сообщении изложить вопрос или проблему, с которой столкнулись, а мы рассмотрим её в ближайшее время.', reply_markup=local_keyb)

    async def _generate_phrase(self, message:aiogram.types.Message, user:User):
        if user.actual_limit > 0:
            user.actual_limit -= 1
            await message.answer(f'🔑 Осталось фраз на сегодня: {user.actual_limit}.')
            await self._user_storage.decrease_phrases(user)
            local_keyb = self._generate_menu_keyb(user)
            phrase = await self._phrases_storage.get_random_phrase()
            await message.answer(f"`{phrase}`", parse_mode=aiogram.types.ParseMode.MARKDOWN, reply_markup=local_keyb)

    async def _get_profile_info(self, message:aiogram.types.Message, user:User):
        name_dict = {User.USER:'Отсутствует', User.PAID:'Куплен', User.ADMIN:'Администратор'}
        await message.answer(f"👤 Ваш профиль:\n\n├ ID: `{user.id}`\n├ Ваш никнейм: `{message['from']['username']}`\n├ Ваше имя: `{message['from']['first_name']}`\n├ Наличие доступа: `{name_dict[user.role]}`\n\n├ Реферальная ссылка:\n├ `https://t.me/chance_wallet_bot?start={user.id}`", parse_mode=aiogram.types.ParseMode.MARKDOWN)

    async def _get_qa_info(self, message:aiogram.types.Message, user:User):
        qa_link_keyboard = InlineKeyboardMarkup().row(InlineKeyboardButton(text='ВОПРОС-ОТВЕТ', url='https://telegra.ph/VOPROS-OTVET-07-13-2'))
        await message.answer(text='📑 Прочитайте статью, которую мы подготовили для вас:', reply_markup=qa_link_keyboard)
        await message.answer(text='⁉️ Не нашли ответ на свой вопрос? - @petorlov\n\nПостарайтесь коротко и в одном сообщении изложить вопрос или проблему, с которой столкнулись, а мы рассмотрим её в ближайшее время.')

    async def _switch_to_admin_panel(self, message:aiogram.types.Message, user:User):
        await message.answer('Панель навигации администратора:', reply_markup=self._admin_panel)
    
    async def _ask_unpaid_id(self, message:aiogram.types.Message, user:User):
        await message.answer('Пришлите id пользователя, у которого хотите забрать доступ, ОТМЕНА для отмены')
        await GetAnswer.answer_unpaid_id.set()

    async def _set_unpaid_id(self, message:aiogram.types.Message, state:aiogram.dispatcher.FSMContext):
        if message.text == "ОТМЕНА":
            await message.answer('Успешно отменено')
        elif message.text.isdigit():
            db_user = await self._user_storage.get_by_id(int(message.text))
            if db_user is not None:
                if db_user.role == User.BLOCKED:
                    await message.answer('Пользователь заблокирован')
                if db_user.role == User.PAID:
                    await self._user_storage.remove_paid(db_user)
                    local_keyb = self._generate_menu_keyb(db_user)
                    await self._bot.send_message(chat_id=db_user.id, text="Ваш доступ был аннулирован.", reply_markup=local_keyb)
                    await self._user_storage.change_phrase_limit(db_user, -10)
                    await message.answer('Пользователь больше не считается оплаченым')
                else:
                    await message.answer('Этот пользователь уже не имеет статус оплатившего')
            else:
                await message.answer('Такого пользователя не найдено')
        else:
            await message.answer('Неправильный формат')
        await state.finish()

    async def _ask_paid_id(self, message:aiogram.types.Message, user:User):
        await message.answer('Пришлите id оплатившего пользователя, ОТМЕНА для отмены')
        await GetAnswer.answer_paid_id.set()
    
    async def _set_paid_id(self, message:aiogram.types.Message, state:aiogram.dispatcher.FSMContext):
        if message.text == "ОТМЕНА":
            await message.answer('Успешно отменено.')
        elif message.text.isdigit():
            db_user = await self._user_storage.get_by_id(int(message.text))
            if db_user is not None:
                if db_user.role == User.BLOCKED:
                    await message.answer('Пользователь заблокирован')
                if db_user.role != User.PAID:
                    await self._user_storage.add_paid(db_user)
                    local_keyb = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("✒️ Начать обучение")).row(KeyboardButton("↘️ Пропустить"))
                    await self._bot.send_message(chat_id=db_user.id, text="💌 Я очень рад, что ты приобрёл мой продукт. Я уверен - он тебя не разочарует.\n\nПришло время автоматизировать процесс поиска забытых кошельков. Давай я тебя всему научу, а тебе останется только ждать своей первой прибыли.\n\n💸💸💸💸💸", reply_markup=local_keyb)
                    await self._user_storage.change_phrase_limit(db_user, 10)
                    await message.answer('Пользователь успешно добавлен')
                else:
                    await message.answer('Этот пользователь уже имеет статус оплатившего')
            else:
                await message.answer('Такого пользователя не найдено')
        else:
            await message.answer('Неправильный формат')
        await state.finish()

    async def _access_users_list(self, message:aiogram.types.Message, user:User):
        users = await self._user_storage.get_role_list(User.PAID)
        if users is None or len(users) == 0:
            await message.answer('Оплативших доступ нет')
        else:
            users = map(lambda x:str(x), users)
            async with aiofiles.open('paid_users.txt', 'w') as f:
                await f.write("\n".join(users))
            async with aiofiles.open('paid_users.txt', 'rb') as f:
                await message.answer_document(f)

    async def _users_amount(self, message:aiogram.types.Message, user:User):
        users = await self._user_storage.get_user_amount()
        await message.answer(f'Количество пользователей: {users}')

    async def _increase_limits(self, message:aiogram.types.Message, user:User):
        await message.answer('Пришлите id пользователя и изменение его лимита через пробел')
        await GetAnswer.answer_limit.set()
    
    async def _update_user_limit(self, message:aiogram.types.Message, state:aiogram.dispatcher.FSMContext):
        user_id, limit_delta = map(lambda x: int(x), message.text.split())
        user = await self._user_storage.get_by_id(user_id)
        if user is None:
            await message.answer('Пользователь с таким id не найден')
        elif user.role == User.BLOCKED:
            await message.answer('Пользователь заблокирован, выдача лимитов ему бесполезна')
        else:
            await self._user_storage.change_phrase_limit(user, limit_delta)
            await message.answer(f'Лимит пользователя с id {user_id} успешно изменен на {limit_delta}')
        await state.finish()

    async def _buy_db(self, message:aiogram.types.Message, user:User):
        async with aiofiles.open('pics/bd.jpg', 'rb') as f:
            await message.answer_photo(photo=f,caption="БАЗА ДАННЫХ с BTC кошельками - ключевой момент в майнинге подобного вида. Чем больше кошельков - тем выше шанс найти что-то в них.\n\nВы можете приобрести кошельки как оптом, так и базами по отдельности.\n\n+50.000 строк - 5$\n+500.000 строк - 45$\n+1.000.000 строк - 75$\n+5.000.000 строк - 300$\n\nБолее крупные суммы обговариваются лично.\n\nАДРЕССА КРИПТОКОШЕЛЬКОВ ДЛЯ ОПЛАТЫ\n\nЕсли этот способ не подходит пиши в ЛС: @petorlov\n\nUSDT (TRC-20)\n`TTrHm2BYcfBTFoTqNp2ZW5VefPe5yG2oF6`", parse_mode=aiogram.types.ParseMode.MARKDOWN)
        local_keyb = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton("✅ Я оплатил")).row(KeyboardButton("ℹ️ Консультация"), KeyboardButton("↘️ Ещё подумаю"))
        await message.answer('⬇️⬇️⬇️ После совершения оплаты выберите пункт "я оплатил", после чего отправьте нам хеш или ссылку перевода.', reply_markup=local_keyb)

    async def _buy_program(self, message:aiogram.types.Message, user:User):
        async with aiofiles.open('pics/program_buy.jpg', 'rb') as f:
            await message.answer_photo(f, "На данный момент у нас одна собственно разработанная программа для поиска монеты BTC.\n\nПринцип работы абсолютно идентичен с тем, что был показан во время обучения. Главное отличие в скорости и абсолютной автоматизации, которое мы предлагаем.")
        local_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton(text="❓ Сколько стоит?")).row(KeyboardButton(text="❓️ Вопрос-ответ"))
        await message.answer("Покупая программу, вы автоматически соглашаетесь с тем, что ознакомились со статьей вопросы-ответы. Это важно для вас и для нас.\n\nМы постарались сделать бота максимально простым, но информативным. Большинство ответов на свои вопросы вы найдёте в этом боте. Также вы можете задать вопрос администратору — @petorlov", reply_markup=local_keyboard)
    
    async def _how_much(self, message:aiogram.types.Message, user:User):
        async with aiofiles.open('pics/price.jpg', 'rb') as f:
            await message.answer_photo(f, "СТОИМОСТЬ ДОСТУПА: 60$ (3840 руб.)\nАДРЕС КРИПТОКОШЕЛЬКА ДЛЯ ОПЛАТЫ\n\nЕсли этот способ не подходит пиши в ЛС: @petorlov\n\n60 USDT (TRC-20)\n`TTrHm2BYcfBTFoTqNp2ZW5VefPe5yG2oF6`\n\nQIWI Card / VISA / MS / Юмани и другое.\n\nТакже возможна оплата через гаранта.", parse_mode=aiogram.types.ParseMode.MARKDOWN)
        local_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton(text="✅ Я оплатил")).row(KeyboardButton(text="ℹ️ Консультация"), KeyboardButton(text="↘️ Ещё подумаю"))
        await message.answer('⬇️⬇️⬇️ После совершения оплаты выберите пункт "я оплатил", после чего отправьте нам хеш или ссылку перевода.', reply_markup=local_keyboard)
    
    async def _hash_link_await(self, message:aiogram.types.Message, user:User):
        await message.answer("⬇️⬇️⬇️ Теперь отправьте нам хеш или ссылку перевода.", reply_markup=aiogram.types.ReplyKeyboardRemove())
        await GetAnswer.hash_link_await.set()

    async def _payment_await(self, message:aiogram.types.Message, state:aiogram.dispatcher.FSMContext):
        user = await self._user_storage.get_by_id(message.chat.id)
        local_keyb = self._generate_menu_keyb(user)
        await message.answer("😻 Ваш запрос вскоре будет обработан.", reply_markup=local_keyb)
        await state.finish()
        access = {User.USER:'Отсутствует', User.PAID:'Куплен', User.ADMIN:"Куплен"}
        items = {User.PAID:"докупку ДБ", User.ADMIN:"докупку ДБ", User.USER:"оплату"}
        text = f"💰 Поступил новый запрос на {items[user.role]}.\n\nДоказательства платежа от пользователя:\n\n{message.text}\n\n👤 Профиль пользователя:\n\nID: {user.id}\nНикнейм: {message.from_user.username}\nИмя: {message.from_user.first_name}\nНаличие доступа: {access[user.role]}"
        await self._bot.send_message(chat_id=Config.admins_chat_id, text=text)
    
    async def _add_phrase(self, message:aiogram.types.Message, user:User):
        phrase_text = message.text[8:]
        await self._phrases_storage.create(phrase_text)
        await message.answer(f'Фраза "{phrase_text}" добавлена')

    async def _add_phrases(self, message:aiogram.types.Message, user:User):
        await message.answer('Отправьте txt файл с фразамию')
        await GetAnswer.phrases_file.set()
    
    async def _process_phrases(self, message:aiogram.types.Message, state:aiogram.dispatcher.FSMContext):
        if message.document and message.document.file_name.split(".")[-1] == "txt":
            # await self._bot.download_file_by_id(message.document.file_id, "./")   
            async with aiofiles.open(message.document.file_name, 'r') as f:
                phrases = await f.readlines()
            await state.finish()
            await message.answer('Фразы успешно добавлены')
            for phrase in phrases:
                await self._phrases_storage.create(phrase)
        else:
            await message.answer('Неправильный формат файла, попробуйте снова')
            await state.finish()

    async def _phrases_amount(self, message:aiogram.types.Message, user:User):
        users = await self._phrases_storage.get_phrases_amount()
        await message.answer(f'Количество фраз: {users}')

    async def _download_program(self, message:aiogram.types.Message, user:User):
        local_keyb = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton(text='MacOS'), KeyboardButton(text='Windows')).row(KeyboardButton(text="Android"), KeyboardButton(text="IOS"))
        await message.answer("💌 Я очень рад, что ты приобрёл мой продукт. Я уверен - он тебя не разочарует.\n\nПришло время автоматизировать процесс поиска забытых кошельков. Давай я тебя всему научу, а тебе останется только ждать своей первой прибыли.\n\nМы предоставляем полную поддержку в течение 24 часов, в которые ты всегда можешь написать мне свой вопрос или попросить помощи.\n\n💸💸💸💸💸", reply_markup=local_keyb)

    async def _send_win_tutorial(self, message:aiogram.types.Message, user:User):
        async with aiofiles.open('pics/mining.jpg', 'rb') as f:
            await message.answer_photo(f,"Майнинг v2.0 - продукт будущего. Программа позволяет с высокой скоростью майнить криптокошельки, подбирая кодовые фразы.\n\nОсновной уклон происходит на базы данных. Чем больше у вас кошельков - тем выше шанс что-то найти.\n\nПри желании вы можете докупить БД для программы. Каждые +50.000 кошельков обойдутся всего в 5$.")
        links_keyb = InlineKeyboardMarkup().row(InlineKeyboardButton(text="Скачать программу", url="https://clck.ru/sM9od")).row(InlineKeyboardButton(text="Скачать Python", url='https://www.python.org/ftp/python/3.10.5/python-3.10.5-amd64.exe')).row(InlineKeyboardButton(text='Скачать базу данных(100к)', url='https://clck.ru/sHDtn'))
        await message.answer('Все компоненты программы доступны по ссылкам ниже:', reply_markup = links_keyb)
        local_keyb = self._generate_menu_keyb(user)
        await message.answer("🔔 Не отключай уведомления, у нас часто бывают розыгрыши БД!", reply_markup=local_keyb)
    
    async def _send_macos_tutorial(self, message:aiogram.types.Message, user:User):
        async with aiofiles.open('pics/mining.jpg', 'rb') as f:
            await message.answer_photo(f,"Майнинг v2.0 - продукт будущего. Программа позволяет с высокой скоростью майнить криптокошельки, подбирая кодовые фразы.\n\nОсновной уклон происходит на базы данных. Чем больше у вас кошельков - тем выше шанс что-то найти.\n\nПри желании вы можете докупить БД для программы. Каждые +50.000 кошельков обойдутся всего в 5$.")
        links_keyb = InlineKeyboardMarkup().row(InlineKeyboardButton(text="Скачать программу", url="https://clck.ru/sM9od")).row(InlineKeyboardButton(text="Скачать Python", url='https://www.python.org/ftp/python/3.10.5/python-3.10.5-amd64.exe')).row(InlineKeyboardButton(text='Скачать базу данных(100к)', url='https://clck.ru/sHDtn'))
        await message.answer('1) Устанавливаете докер (https://docs.docker.com/desktop/install/mac-install/).\n\n2) Скачиваете программу (ту, что скинул ниже).\n\n3) Открываете терминал и пишете в него:\n\ncd папка где лежит проект\n\n4) Далее вписываете в терминал:\n\ndocker compose up —build\n\nПеред «build» два тире.\n\n5) Ждете завершения установки, в первый раз программа будет запускаться долго, а далее уже быстро.', reply_markup = links_keyb)
        local_keyb = self._generate_menu_keyb(user)
        await message.answer("🔔 Не отключай уведомления, у нас часто бывают розыгрыши БД!", reply_markup=local_keyb)
    
    async def _send_android_tutorial(self, message:aiogram.types.Message, user:User):
        await message.answer("Вся информация по усстановке в файле:")
        local_keyb = self._generate_menu_keyb(user)
        async with aiofiles.open('android.txt', 'rb') as f:
            await message.answer_document(f, reply_markup=local_keyb)

    async def _send_ios_tutorial(self, message:aiogram.types.Message, user:User):
        local_keyb = self._generate_menu_keyb(user)
        await message.answer('Пока не готово.', reply_markup=local_keyb)

    async def _promote_to_admin(self, message:aiogram.types.Message, user:User):
        admin_id = message.text.split()[1]
        user = await self._user_storage.get_by_id(int(admin_id))
        if user is not None:
            if user.role in (User.ADMIN, User.BLOCKED):
                match user.role:
                    case User.ADMIN:
                        await message.answer('Пользователь уже админ')
                    case User.BLOCKED:
                        await message.answer('Пользователь заблокирован')
            else:
                await self._user_storage.promote_to_admin(int(admin_id))
                await message.answer(f'Роль администратора выдана по id {admin_id}')
        else:
            await message.answer(f'Пользователя с id {admin_id} не найдено')
    
    async def _demote_from_admin(self, message:aiogram.types.Message, user:User):
        admin_id = message.text.split()[1]
        user = await self._user_storage.get_by_id(int(admin_id))
        if user is not None:
            if user.role == User.ADMIN:
                await self._user_storage.demote_from_admin(int(admin_id))
                await message.answer(f'Пользователь {admin_id} больше не администратор.')
            else:
                await message.answer(f'Пользователь {admin_id} и так не админ.')
        else:
            await message.answer(f'Пользователя с id {admin_id} не найдено')

    def _init_handler(self):
        self._dispatcher.register_message_handler(self._user_middleware(self._god_required(self._demote_from_admin)), commands=['remove_admin'])
        self._dispatcher.register_message_handler(self._user_middleware(self._god_required(self._promote_to_admin)), commands=['add_admin'])
        self._dispatcher.register_message_handler(self._user_middleware(self._admin_required(self._add_phrase)), commands=['phrase'])
        self._dispatcher.register_message_handler(self._user_middleware(self._admin_required(self._add_phrases)), commands=['phrases'])
        self._dispatcher.register_message_handler(self._process_phrases, state=GetAnswer.phrases_file, content_types=aiogram.types.message.ContentType.ANY)
        self._dispatcher.register_message_handler(self._user_middleware(self._admin_required(self._phrases_amount)), commands=['phrase_amount'])
        self._dispatcher.register_message_handler(self._user_middleware(self._show_menu), commands=['start', 'menu'])
        self._dispatcher.register_message_handler(self._user_middleware(self._show_menu), text='✅ Начать майнить')
        self._dispatcher.register_message_handler(self._user_middleware(self._show_menu), text='↘️ Пропустить')
        self._dispatcher.register_message_handler(self._user_middleware(self._will_think), text='↘️ Ещё подумаю')
        self._dispatcher.register_message_handler(self._user_middleware(self._show_menu), text='Меню')
        self._dispatcher.register_message_handler(self._user_middleware(self._check_subscription), text='✅ Проверить подписку')
        self._dispatcher.register_message_handler(self._user_middleware(self._start_education), text='✨Начать обучение')
        self._dispatcher.register_message_handler(self._user_middleware(self._start_education), text='✒️ Обучение')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._start_paid_education)), text='✒️ Начать обучение')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._step1_paid_education)), text='WINDOWS')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._step2_paid_education)), text='⤵️ Я скачал и установил Python')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._step3_paid_education)), text='⤵️ Я скачал и установил библиотеку')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._step4_paid_education)), text='⤵️ Я скачал программу')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._step5_paid_education)), text='⤵️ Я скачал базу данных')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._step6_paid_education)), text='✅ Завершить обучение')
        self._dispatcher.register_message_handler(self._user_middleware(self._step2_education), text='⤵️ Шаг 1')
        self._dispatcher.register_message_handler(self._user_middleware(self._step3_education), text='⤵️ Я создал кошелёк')
        self._dispatcher.register_message_handler(self._user_middleware(self._step4_education), text='✨ Сгенерировать фразу')
        self._dispatcher.register_message_handler(self._user_middleware(self._step5_education), text='✅ Готово')
        self._dispatcher.register_message_handler(self._user_middleware(self._get_support_info), text='ℹ️ Консультация')
        self._dispatcher.register_message_handler(self._user_middleware(self._get_support_info), text='✉️ Поддержка')
        self._dispatcher.register_message_handler(self._user_middleware(self._get_profile_info), text='👤 Мой ID')
        self._dispatcher.register_message_handler(self._user_middleware(self._get_qa_info), text='❓️ Вопрос-ответ')
        self._dispatcher.register_message_handler(self._user_middleware(self._generate_phrase), aiogram.dispatcher.filters.Text(startswith="✨ Генерировать фразу "))
        self._dispatcher.register_message_handler(self._user_middleware(self._admin_required(self._switch_to_admin_panel)), text='↕️ Админка')
        self._dispatcher.register_message_handler(self._user_middleware(self._admin_required(self._ask_paid_id)), text='Выдать доступ')
        self._dispatcher.register_message_handler(self._user_middleware(self._admin_required(self._ask_unpaid_id)), text='Забрать доступ')
        self._dispatcher.register_message_handler(self._user_middleware(self._admin_required(self._access_users_list)), text='Список клиентов')
        self._dispatcher.register_message_handler(self._user_middleware(self._admin_required(self._users_amount)), text='Количество пользователей')
        self._dispatcher.register_message_handler(self._user_middleware(self._admin_required(self._increase_limits)), text='Увеличить лимиты')
        self._dispatcher.register_message_handler(self._set_paid_id, state=GetAnswer.answer_paid_id)
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._buy_db)), text='✅ Докупить БД')
        self._dispatcher.register_message_handler(self._user_middleware(self._buy_program), text='✅ Купить программу')
        self._dispatcher.register_message_handler(self._user_middleware(self._how_much), text='❓ Сколько стоит?')
        self._dispatcher.register_message_handler(self._user_middleware(self._hash_link_await), text='✅ Я оплатил')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._download_program)), text='↙️ Скачать программу')
        self._dispatcher.register_message_handler(self._payment_await, state=GetAnswer.hash_link_await)
        self._dispatcher.register_message_handler(self._set_unpaid_id, state=GetAnswer.answer_unpaid_id)
        self._dispatcher.register_message_handler(self._update_user_limit, state=GetAnswer.answer_limit)
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._send_win_tutorial)), text='Windows')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._send_macos_tutorial)), text='MacOS')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._send_android_tutorial)), text='Android')
        self._dispatcher.register_message_handler(self._user_middleware(self._paid_required(self._send_ios_tutorial)), text='IOS')
    
    def _user_middleware(self, func:typing.Callable) -> typing.Callable:
        async def wrapper(message:aiogram.types.Message, *args, **kwargs):
            user:ChatMember = await self._bot.get_chat_member(chat_id=Config.channel_id, user_id=message.chat.id)
            if user.status in ['member', 'creator', 'administrator']:
                user = await self._user_storage.get_by_id(message.chat.id)
                if user is None:
                    split_message = message.text.split()
                    if len(split_message) == 2 and split_message[1].isdigit() and await self._user_storage.get_by_id(int(split_message[1])):
                        inviter_id = int(split_message[1])
                        await self._user_storage.give_referal(inviter_id)
                        inviter_user = self._user_storage.get_by_id(inviter_id)
                        local_keyb = self._generate_menu_keyb(inviter_user)
                        await self._bot.send_message(chat_id=inviter_id, text='❤️ Спасибо за приглашённого друга.\n\nКак и обещали - зачислили тебе 30 генераций!', reply_markup = local_keyb)
                    user = User(
                        id = message.chat.id,
                        role = User.USER,
                        actual_limit=10,
                        daily_limit=10
                    )
                    await self._user_storage.create(user)
                elif user.role == User.BLOCKED:
                    pass
                else:
                    await func(message, user)
            else:
                check_channel_subcription_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton(text='✅ Проверить подписку'))
                await message.answer('Для того, чтобы получить доступ к боту, тебе следует подписаться на @cryptolabv2', reply_markup=check_channel_subcription_keyboard)
                channel_subcription_keyboard = InlineKeyboardMarkup().row(InlineKeyboardButton(text='Подписаться', url='https://t.me/cryptolabv2'))
                await message.answer('Оформить подписку на канал:', reply_markup=channel_subcription_keyboard)
        return wrapper
    
    def _admin_required(self, func:typing.Callable) -> typing.Callable:
        async def wrapper(message:aiogram.types.Message, user:User, *args, **kwargs):
            if user.role == User.ADMIN:
                await func(message, user)
        return wrapper
    
    def _paid_required(self, func:typing.Callable) -> typing.Callable:
        async def wrapper(message:aiogram.types.Message, user:User, *args, **kwargs):
            if user.role in (User.PAID, User.ADMIN) or user.id in Config.gods:
                await func(message, user)
        return wrapper

    def _god_required(self, func:typing.Callable) -> typing.Callable:
        async def wrapper(message:aiogram.types.Message, user:User, *args, **kwargs):
            if user.id in Config.gods:
                await func(message, user)
        return wrapper

    def _create_keyboards(self):
        self._menu_keyboard_user = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('👤 Мой ID'),KeyboardButton('✒️ Обучение'))\
                .row(KeyboardButton('❓️ Вопрос-ответ'), KeyboardButton('✉️ Поддержка'))\
                    .row(KeyboardButton("✅ Купить программу"))

        self._menu_keyboard_user_access = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('👤 Мой ID'),KeyboardButton('✒️ Обучение'))\
                .row(KeyboardButton('✅ Докупить БД'), KeyboardButton('✉️ Поддержка'))\
                    .row(KeyboardButton("↙️ Скачать программу"))

        self._menu_keyboard_admin = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('👤 Мой ID'),KeyboardButton('✒️ Обучение'))\
                .row(KeyboardButton('✅ Докупить БД'), KeyboardButton('↕️ Админка'))\
                    .row(KeyboardButton("↙️ Скачать программу"))
        
        self._checked_subscription_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('✨Начать обучение')).row(KeyboardButton('↘️ Пропустить'))\
                .row(KeyboardButton("✅ Купить программу"))
        
        self._checked_subscription_keyboard_access = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('✨Начать обучение')).row(KeyboardButton('↘️ Пропустить'))\
                .row(KeyboardButton("↙️ Скачать программу"))
        
        self._admin_panel = ReplyKeyboardMarkup(resize_keyboard=True)\
            .row(KeyboardButton('Выдать доступ'), KeyboardButton('Забрать доступ'), KeyboardButton('Увеличить лимиты'))\
                .row(KeyboardButton('Количество пользователей'), KeyboardButton('Список клиентов'))\
                    .row(KeyboardButton('Меню'))
