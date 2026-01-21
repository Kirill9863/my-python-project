# -*- coding: utf-8 -*-
# --- 1. ИМПОРТЫ ---
import os
os.environ['KIVY_TEXT'] = 'pil'
import mysql.connector
from datetime import date
from functools import partial
import csv
import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp

kivy.require('2.1.0')

# --- 2. НАСТРОЙКИ ТЕМЫ И СТИЛЕЙ ---
THEMES = {
    'Светлая': {
        'bg': (0.95, 0.95, 0.95, 1), 'text': (0, 0, 0, 1),
        'primary': (0.2, 0.5, 0.8, 1), 'secondary_bg': (0.9, 0.9, 0.9, 1),
        'input_bg': (1, 1, 1, 1), 'button_text': (1, 1, 1, 1),
        'list_item_bg': (0.85, 0.85, 0.85, 1), 'popup_bg': (1, 1, 1, 1),
    },
    'Тёмная': {
        'bg': (0.1, 0.1, 0.1, 1), 'text': (0.9, 0.9, 0.9, 1),
        'primary': (0.3, 0.6, 0.9, 1), 'secondary_bg': (0.2, 0.2, 0.2, 1),
        'input_bg': (0.15, 0.15, 0.15, 1), 'button_text': (1, 1, 1, 1),
        'list_item_bg': (0.25, 0.25, 0.25, 1), 'popup_bg': (0.18, 0.18, 0.18, 1),
    }
}

# Настройка соединения с базой данных
MYSQL_CONFIG = {
    'host': 'pma.goncharuk.info',
    'port': 3306,
    'user': 'phpmyadmin',
    'password': '0907',
    'database': 'phpmyadmin'
}

def connect():
    return mysql.connector.connect(**MYSQL_CONFIG)

# ------------------- ФУНКЦИИ РАБОТЫ С БД -------------------
def export_data(file_path, data_type):
    conn = connect()
    cursor = conn.cursor()
    if data_type == 'persons':
        cursor.execute("SELECT * FROM persons")
    elif data_type == 'events':
        cursor.execute("SELECT * FROM events")
    elif data_type == 'places':
        cursor.execute("SELECT * FROM places")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)
    conn.close()

def import_data(file_path, data_type):
    conn = connect()
    cursor = conn.cursor()
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Пропускаем заголовки
        if data_type == 'persons':
            insert_query = "INSERT INTO persons (name, dates, biography) VALUES (%s, %s, %s)"
        elif data_type == 'events':
            insert_query = "INSERT INTO events (event_title, start_date, end_date, description, significance) VALUES (%s, %s, %s, %s, %s)"
        elif data_type == 'places':
            insert_query = "INSERT INTO places (place_name, location, historical_period) VALUES (%s, %s, %s)"
        cursor.executemany(insert_query, list(reader))
    conn.commit()
    conn.close()

def get_setting(setting_id, default=None):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE id=%s", (setting_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else default

def save_setting(setting_id, setting_value):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO settings (id, value) VALUES (%s, %s)
                      ON DUPLICATE KEY UPDATE value=%s""",
                   (setting_id, setting_value, setting_value))
    conn.commit()
    conn.close()

def _count(table):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    cnt = cursor.fetchone()[0]
    conn.close()
    return cnt

def count_persons(): return _count('persons')
def count_events():  return _count('events')
def count_places():  return _count('places')

def _search(table, field, query):
    conn = connect()
    cursor = conn.cursor()
    sql = f"SELECT id, {field} FROM {table} WHERE {field} LIKE %s ORDER BY {field}"
    cursor.execute(sql, ('%' + query + '%',))
    res = cursor.fetchall()
    conn.close()
    return res

def get_persons(search_query=""): return _search('persons', 'name', search_query)
def get_events(search_query=""):  return _search('events',  'event_title', search_query)
def get_places(search_query=""):  return _search('places',  'place_name', search_query)

def _details(table, obj_id, fields):
    conn = connect()
    cursor = conn.cursor()
    sql = f"SELECT {', '.join(fields)} FROM {table} WHERE id=%s"
    cursor.execute(sql, (obj_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_person_details(person_id): return _details('persons', person_id, ['name', 'dates', 'biography'])
def get_event_details(event_id):   return _details('events',   event_id, ['event_title', 'start_date', 'end_date', 'description', 'significance'])
def get_place_details(place_id):   return _details('places',   place_id, ['place_name', 'location', 'historical_period'])

def _delete(table, obj_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id=%s", (obj_id,))
    conn.commit()
    conn.close()

def delete_person(person_id): _delete('persons', person_id)
def delete_event(event_id):   _delete('events',   event_id)
def delete_place(place_id):   _delete('places',   place_id)

def _add(table, values, fields, unique_name):
    try:
        conn = connect()
        cursor = conn.cursor()
        placeholders = ', '.join(['%s'] * len(values))
        sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"
        cursor.execute(sql, values)
        conn.commit()
        conn.close()
        return True, None
    except mysql.connector.IntegrityError:
        return False, f"{table[:-1].capitalize()} с именем '{unique_name}' уже существует!"

def add_person(name, dates, biography): return _add('persons', (name, dates, biography), ['name', 'dates', 'biography'], name)
def add_event(event_title, start_date, end_date, description, significance):
    return _add('events', (event_title, start_date, end_date, description, significance),
                ['event_title', 'start_date', 'end_date', 'description', 'significance'], event_title)
def add_place(place_name, location, historical_period):
    return _add('places', (place_name, location, historical_period),
                ['place_name', 'location', 'historical_period'], place_name)

def _update(table, obj_id, values):
    conn = connect()
    cursor = conn.cursor()
    fields = {
        'persons': ['name', 'dates', 'biography'],
        'events':  ['event_title', 'start_date', 'end_date', 'description', 'significance'],
        'places':  ['place_name', 'location', 'historical_period']
    }[table]
    set_clause = ', '.join([f"{f}=%s" for f in fields])
    sql = f"UPDATE {table} SET {set_clause} WHERE id=%s"
    cursor.execute(sql, values + [obj_id])
    conn.commit()
    conn.close()

def update_person(person_id, name, dates, biography): _update('persons', person_id, [name, dates, biography])
def update_event(event_id, event_title, start_date, end_date, description, significance):
    _update('events', event_id, [event_title, start_date, end_date, description, significance])
def update_place(place_id, place_name, location, historical_period):
    _update('places', place_id, [place_name, location, historical_period])

# ------------------- POPUP-КЛАССЫ -------------------
class PersonDetailsPopup(Popup):
    def __init__(self, person_id, on_save_callback, **kwargs):
        super().__init__(**kwargs)
        self.person_id = person_id
        self.on_save_callback = on_save_callback
        self.edit_mode = False
        self.title = "Добавление новой личности" if person_id is None else "Информация о личности"
        self.size_hint = (0.8, 0.8)
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.add_widget(layout)
        self.name_input = TextInput(hint_text='Имя', font_size='18sp')
        self.dates_input = TextInput(hint_text='Даты жизни', size_hint_y=None, height=dp(40))
        self.biography_input = TextInput(hint_text='Биография...')
        self.status_label = Label(size_hint_y=None, height=dp(30))
        self.control_buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.edit_button = Button(text="Редактировать", on_press=self.toggle_edit_mode)
        self.delete_button = Button(text="Удалить", on_press=self.confirm_delete)
        self.save_button = Button(text="Сохранить", on_press=self.save_person)
        self.cancel_button = Button(text="Отменить", on_press=self.cancel_edit)
        layout.add_widget(self.name_input)
        layout.add_widget(self.dates_input)
        layout.add_widget(self.biography_input)
        layout.add_widget(self.status_label)
        layout.add_widget(self.control_buttons)
        if person_id is not None:
            self.load_details()
            self.set_fields_readonly(True)
            self.control_buttons.add_widget(self.edit_button)
            self.control_buttons.add_widget(self.delete_button)
        else:
            self.edit_mode = True
            self.set_fields_readonly(False)
            self.control_buttons.add_widget(self.save_button)
        self.apply_theme()

    def apply_theme(self):
        theme = THEMES[App.get_running_app().current_theme]
        self.background_color = theme['popup_bg']
        for w in self.walk():
            if isinstance(w, Label): w.color = theme['text']
            if isinstance(w, TextInput):
                w.background_color, w.foreground_color = theme['input_bg'], theme['text']
            if isinstance(w, Button):
                w.background_color, w.color = theme['primary'], theme['button_text']

    def load_details(self):
        details = get_person_details(self.person_id)
        if details and len(details) == 3:
            self.name_input.text = str(details[0]) if details[0] is not None else ''
            self.dates_input.text = str(details[1]) if details[1] is not None else ''
            self.biography_input.text = str(details[2]) if details[2] is not None else ''
        else:
            self.name_input.text = ''
            self.dates_input.text = ''
            self.biography_input.text = ''

    def set_fields_readonly(self, state):
        for inp in (self.name_input, self.dates_input, self.biography_input):
            inp.readonly = state

    def toggle_edit_mode(self, _):
        self.edit_mode = True
        self.set_fields_readonly(False)
        self.control_buttons.clear_widgets()
        self.control_buttons.add_widget(self.save_button)
        self.control_buttons.add_widget(self.cancel_button)

    def confirm_delete(self, _):
        confirm = Popup(title="Подтверждение удаления",
                        content=Label(text="Вы уверены, что хотите удалить эту личность?"),
                        size_hint=(None, None), size=(dp(400), dp(200)))
        box = BoxLayout(orientation='horizontal', spacing=dp(10))
        yes = Button(text="Да", on_release=lambda _: self.delete_and_close(confirm))
        no = Button(text="Нет", on_release=confirm.dismiss)
        box.add_widget(yes)
        box.add_widget(no)
        confirm.content = box
        confirm.open()

    def delete_and_close(self, confirm):
        delete_person(self.person_id)
        self.on_save_callback()
        confirm.dismiss()
        self.dismiss()

    def cancel_edit(self, _):
        self.edit_mode = False
        self.set_fields_readonly(True)
        self.control_buttons.clear_widgets()
        self.control_buttons.add_widget(self.edit_button)
        self.control_buttons.add_widget(self.delete_button)
        self.load_details()
        self.status_label.text = ""

    def save_person(self, _):
        name = self.name_input.text.strip()
        if not name:
            self.status_label.text = "Ошибка: Имя не может быть пустым!"
            return
        dates = self.dates_input.text.strip()
        bio = self.biography_input.text.strip()
        if self.person_id:
            update_person(self.person_id, name, dates, bio)
        else:
            success, msg = add_person(name, dates, bio)
            if not success:
                self.status_label.text = msg
                return
        self.on_save_callback()
        self.dismiss()

class EventDetailsPopup(Popup):
    def __init__(self, event_id, on_save_callback, **kwargs):
        super().__init__(**kwargs)
        self.event_id = event_id
        self.on_save_callback = on_save_callback
        self.edit_mode = False
        self.title = "Добавление нового события" if event_id is None else "Информация о событии"
        self.size_hint = (0.8, 0.8)
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.add_widget(layout)
        self.event_title_input = TextInput(hint_text='Название события', font_size='18sp')
        self.start_date_input = TextInput(hint_text='Начало события', size_hint_y=None, height=dp(40))
        self.end_date_input = TextInput(hint_text='Окончание события', size_hint_y=None, height=dp(40))
        self.description_input = TextInput(hint_text='Описание события...')
        self.significance_input = TextInput(hint_text='Значение события...')
        self.status_label = Label(size_hint_y=None, height=dp(30))
        self.control_buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.edit_button = Button(text="Редактировать", on_press=self.toggle_edit_mode)
        self.delete_button = Button(text="Удалить", on_press=self.confirm_delete)
        self.save_button = Button(text="Сохранить", on_press=self.save_event)
        self.cancel_button = Button(text="Отменить", on_press=self.cancel_edit)
        layout.add_widget(self.event_title_input)
        layout.add_widget(self.start_date_input)
        layout.add_widget(self.end_date_input)
        layout.add_widget(self.description_input)
        layout.add_widget(self.significance_input)
        layout.add_widget(self.status_label)
        layout.add_widget(self.control_buttons)
        if event_id is not None:
            self.load_details()
            self.set_fields_readonly(True)
            self.control_buttons.add_widget(self.edit_button)
            self.control_buttons.add_widget(self.delete_button)
        else:
            self.edit_mode = True
            self.set_fields_readonly(False)
            self.control_buttons.add_widget(self.save_button)
        self.apply_theme()

    def apply_theme(self):
        theme = THEMES[App.get_running_app().current_theme]
        self.background_color = theme['popup_bg']
        for widget in self.walk():
            if isinstance(widget, Label): widget.color = theme['text']
            if isinstance(widget, TextInput):
                widget.background_color, widget.foreground_color = theme['input_bg'], theme['text']
            if isinstance(widget, Button):
                widget.background_color, widget.color = theme['primary'], theme['button_text']

    def load_details(self):
        details = get_event_details(self.event_id)
        if details and len(details) == 5:
            self.event_title_input.text = str(details[0]) if details[0] is not None else ''
            self.start_date_input.text = str(details[1]) if details[1] is not None else ''
            self.end_date_input.text = str(details[2]) if details[2] is not None else ''
            self.description_input.text = str(details[3]) if details[3] is not None else ''
            self.significance_input.text = str(details[4]) if details[4] is not None else ''
        else:
            for field in (self.event_title_input, self.start_date_input,
                          self.end_date_input, self.description_input,
                          self.significance_input):
                field.text = ''

    def set_fields_readonly(self, state):
        for w in (self.event_title_input, self.start_date_input, self.end_date_input,
                  self.description_input, self.significance_input):
            w.readonly = state

    def toggle_edit_mode(self, instance):
        self.edit_mode = True
        self.set_fields_readonly(False)
        self.control_buttons.clear_widgets()
        self.control_buttons.add_widget(self.save_button)
        self.control_buttons.add_widget(self.cancel_button)

    def confirm_delete(self, instance):
        confirm_popup = Popup(title="Подтверждение удаления",
                              content=Label(text="Вы уверены, что хотите удалить это событие?"),
                              size_hint=(None, None), size=(dp(400), dp(200)))
        box = BoxLayout(orientation='horizontal', spacing=dp(10))
        yes_button = Button(text="Да", on_release=lambda _: self.delete_event_and_close(confirm_popup))
        no_button = Button(text="Нет", on_release=confirm_popup.dismiss)
        box.add_widget(yes_button)
        box.add_widget(no_button)
        confirm_popup.content = box
        confirm_popup.open()

    def delete_event_and_close(self, confirm_popup):
        delete_event(self.event_id)
        self.on_save_callback()
        confirm_popup.dismiss()
        self.dismiss()

    def cancel_edit(self, instance):
        self.edit_mode = False
        self.set_fields_readonly(True)
        self.control_buttons.clear_widgets()
        self.control_buttons.add_widget(self.edit_button)
        self.control_buttons.add_widget(self.delete_button)
        self.load_details()
        self.status_label.text = ""

    def save_event(self, instance):
        event_title = self.event_title_input.text.strip()
        if not event_title:
            self.status_label.text = "Ошибка: Название события не может быть пустым!"
            return
        start_date = self.start_date_input.text.strip()
        end_date = self.end_date_input.text.strip()
        description = self.description_input.text.strip()
        significance = self.significance_input.text.strip()
        if self.event_id:
            update_event(self.event_id, event_title, start_date, end_date, description, significance)
        else:
            success, error_msg = add_event(event_title, start_date, end_date, description, significance)
            if not success:
                self.status_label.text = error_msg
                return
        self.on_save_callback()
        self.dismiss()

class PlaceDetailsPopup(Popup):
    def __init__(self, place_id, on_save_callback, **kwargs):
        super().__init__(**kwargs)
        self.place_id = place_id
        self.on_save_callback = on_save_callback
        self.edit_mode = False
        self.title = "Добавление нового места" if place_id is None else "Информация о месте"
        self.size_hint = (0.8, 0.8)
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.add_widget(layout)
        self.place_name_input = TextInput(hint_text='Название места', font_size='18sp')
        self.location_input = TextInput(hint_text='Местоположение', size_hint_y=None, height=dp(40))
        self.historical_period_input = TextInput(hint_text='История места...')
        self.status_label = Label(size_hint_y=None, height=dp(30))
        self.control_buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.edit_button = Button(text="Редактировать", on_press=self.toggle_edit_mode)
        self.delete_button = Button(text="Удалить", on_press=self.confirm_delete)
        self.save_button = Button(text="Сохранить", on_press=self.save_place)
        self.cancel_button = Button(text="Отменить", on_press=self.cancel_edit)
        layout.add_widget(self.place_name_input)
        layout.add_widget(self.location_input)
        layout.add_widget(self.historical_period_input)
        layout.add_widget(self.status_label)
        layout.add_widget(self.control_buttons)
        if place_id is not None:
            self.load_details()
            self.set_fields_readonly(True)
            self.control_buttons.add_widget(self.edit_button)
            self.control_buttons.add_widget(self.delete_button)
        else:
            self.edit_mode = True
            self.set_fields_readonly(False)
            self.control_buttons.add_widget(self.save_button)
        self.apply_theme()

    def apply_theme(self):
        theme = THEMES[App.get_running_app().current_theme]
        self.background_color = theme['popup_bg']
        for widget in self.walk():
            if isinstance(widget, Label): widget.color = theme['text']
            if isinstance(widget, TextInput):
                widget.background_color, widget.foreground_color = theme['input_bg'], theme['text']
            if isinstance(widget, Button):
                widget.background_color, widget.color = theme['primary'], theme['button_text']

    def load_details(self):
        details = get_place_details(self.place_id)
        if details and len(details) == 3:
            self.place_name_input.text = str(details[0]) if details[0] is not None else ''
            self.location_input.text = str(details[1]) if details[1] is not None else ''
            self.historical_period_input.text = str(details[2]) if details[2] is not None else ''
        else:
            self.place_name_input.text = ''
            self.location_input.text = ''
            self.historical_period_input.text = ''

    def set_fields_readonly(self, state):
        for w in (self.place_name_input, self.location_input, self.historical_period_input):
            w.readonly = state

    def toggle_edit_mode(self, instance):
        self.edit_mode = True
        self.set_fields_readonly(False)
        self.control_buttons.clear_widgets()
        self.control_buttons.add_widget(self.save_button)
        self.control_buttons.add_widget(self.cancel_button)

    def confirm_delete(self, instance):
        confirm_popup = Popup(title="Подтверждение удаления",
                              content=Label(text="Вы уверены, что хотите удалить это место?"),
                              size_hint=(None, None), size=(dp(400), dp(200)))
        box = BoxLayout(orientation='horizontal', spacing=dp(10))
        yes_button = Button(text="Да", on_release=lambda _: self.delete_place_and_close(confirm_popup))
        no_button = Button(text="Нет", on_release=confirm_popup.dismiss)
        box.add_widget(yes_button)
        box.add_widget(no_button)
        confirm_popup.content = box
        confirm_popup.open()

    def delete_place_and_close(self, confirm_popup):
        delete_place(self.place_id)
        self.on_save_callback()
        confirm_popup.dismiss()
        self.dismiss()

    def cancel_edit(self, instance):
        self.edit_mode = False
        self.set_fields_readonly(True)
        self.control_buttons.clear_widgets()
        self.control_buttons.add_widget(self.edit_button)
        self.control_buttons.add_widget(self.delete_button)
        self.load_details()
        self.status_label.text = ""

    def save_place(self, instance):
        place_name = self.place_name_input.text.strip()
        if not place_name:
            self.status_label.text = "Ошибка: Название места не может быть пустым!"
            return
        location = self.location_input.text.strip()
        historical_period = self.historical_period_input.text.strip()
        if self.place_id:
            update_place(self.place_id, place_name, location, historical_period)
        else:
            success, error_msg = add_place(place_name, location, historical_period)
            if not success:
                self.status_label.text = error_msg
                return
        self.on_save_callback()
        self.dismiss()

# ------------------- ОСНОВНОЙ ЭКРАН -------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(10), spacing=dp(20))
        self.title_label = Label(text="Историческая Википедия", font_size='20sp', bold=True)
        self.date_label = Label(text=f"Сегодня: {date.today().strftime('%d %B %Y')}", size_hint_x=0.4)
        self.profile_button = Button(text="Профиль", size_hint_x=0.4, on_press=self.go_to_profile)
        header.add_widget(self.title_label)
        header.add_widget(self.date_label)
        header.add_widget(self.profile_button)

        # Actions
        actions_bar = BoxLayout(size_hint_y=None, height=dp(40), padding=dp(5), spacing=dp(10))
        self.export_button = Button(text="Экспорт данных", on_press=self.export_data_popup)
        self.import_button = Button(text="Импорт данных", on_press=self.import_data_popup)
        actions_bar.add_widget(self.export_button)
        actions_bar.add_widget(self.import_button)

        # Tabs
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        tabbed_panel = TabbedPanel(do_default_tab=False)

        # ---- Persons tab ----
        persons_tab = TabbedPanelItem(text="Личности")
        persons_content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.search_person_input = TextInput(hint_text='Поиск по именам...', size_hint_y=None, height=dp(40), multiline=False)
        self.search_person_input.bind(text=self.on_search_person)
        scroll_view_persons = ScrollView()
        self.person_list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.person_list_layout.bind(minimum_height=self.person_list_layout.setter('height'))
        scroll_view_persons.add_widget(self.person_list_layout)
        add_person_btn = Button(text="Добавить новую личность", size_hint_y=None, height=dp(50),
                                on_press=self.add_new_person)
        persons_content.add_widget(self.search_person_input)
        persons_content.add_widget(scroll_view_persons)
        persons_content.add_widget(add_person_btn)
        persons_tab.add_widget(persons_content)

        # ---- Events tab ----
        events_tab = TabbedPanelItem(text="События")
        events_content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.search_event_input = TextInput(hint_text='Поиск по событиям...', size_hint_y=None, height=dp(40), multiline=False)
        self.search_event_input.bind(text=self.on_search_event)
        scroll_view_events = ScrollView()
        self.event_list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.event_list_layout.bind(minimum_height=self.event_list_layout.setter('height'))
        scroll_view_events.add_widget(self.event_list_layout)
        add_event_btn = Button(text="Добавить новое событие", size_hint_y=None, height=dp(50),
                               on_press=self.add_new_event)
        events_content.add_widget(self.search_event_input)
        events_content.add_widget(scroll_view_events)
        events_content.add_widget(add_event_btn)
        events_tab.add_widget(events_content)

        # ---- Places tab ----
        places_tab = TabbedPanelItem(text="Места")
        places_content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.search_place_input = TextInput(hint_text='Поиск по местам...', size_hint_y=None, height=dp(40), multiline=False)
        self.search_place_input.bind(text=self.on_search_place)
        scroll_view_places = ScrollView()
        self.place_list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.place_list_layout.bind(minimum_height=self.place_list_layout.setter('height'))
        scroll_view_places.add_widget(self.place_list_layout)
        add_place_btn = Button(text="Добавить новое место", size_hint_y=None, height=dp(50),
                               on_press=self.add_new_place)
        places_content.add_widget(self.search_place_input)
        places_content.add_widget(scroll_view_places)
        places_content.add_widget(add_place_btn)
        places_tab.add_widget(places_content)

        tabbed_panel.add_widget(persons_tab)
        tabbed_panel.add_widget(events_tab)
        tabbed_panel.add_widget(places_tab)

        content.add_widget(actions_bar)
        content.add_widget(tabbed_panel)
        self.layout.add_widget(header)
        self.layout.add_widget(content)
        self.add_widget(self.layout)
        self.update_theme()

    def export_data_popup(self, _):
        popup = Popup(title="Экспорт данных", size_hint=(0.7, 0.5))
        grid = GridLayout(cols=1, padding=dp(10), spacing=dp(10))
        type_input = TextInput(hint_text="Тип (persons/events/places)")
        path_input = TextInput(hint_text="Путь к файлу (например, data.csv)")
        btn = Button(text="Экспортировать",
                     on_press=lambda __: self._do_export(type_input.text, path_input.text, popup))
        grid.add_widget(type_input)
        grid.add_widget(path_input)
        grid.add_widget(btn)
        popup.content = grid
        popup.open()

    def _do_export(self, data_type, file_path, popup):
        try:
            export_data(file_path, data_type)
            popup.dismiss()
        except Exception as e:
            popup.content = Label(text=f"Ошибка: {e}")

    def import_data_popup(self, _):
        popup = Popup(title="Импорт данных", size_hint=(0.7, 0.5))
        grid = GridLayout(cols=1, padding=dp(10), spacing=dp(10))
        type_input = TextInput(hint_text="Тип (persons/events/places)")
        path_input = TextInput(hint_text="Путь к файлу")
        btn = Button(text="Импортировать",
                     on_press=lambda __: self._do_import(type_input.text, path_input.text, popup))
        grid.add_widget(type_input)
        grid.add_widget(path_input)
        grid.add_widget(btn)
        popup.content = grid
        popup.open()

    def _do_import(self, data_type, file_path, popup):
        try:
            import_data(file_path, data_type)
            popup.dismiss()
        except Exception as e:
            popup.content = Label(text=f"Ошибка: {e}")

    def go_to_profile(self, _): self.manager.current = 'profile'

    def on_search_person(self, _, val): self.populate_person_list(val)
    def on_search_event(self, _, val):  self.populate_event_list(val)
    def on_search_place(self, _, val):  self.populate_place_list(val)

    def populate_person_list(self, query=""):
        self.person_list_layout.clear_widgets()
        theme = THEMES[App.get_running_app().current_theme]
        for pid, name in get_persons(query):
            btn = Button(text=str(name), size_hint_y=None, height=dp(40),
                         background_normal='', background_color=theme['list_item_bg'],
                         color=theme['text'])
            btn.bind(on_press=partial(self.show_person_details, pid))
            self.person_list_layout.add_widget(btn)

    def populate_event_list(self, query=""):
        self.event_list_layout.clear_widgets()
        theme = THEMES[App.get_running_app().current_theme]
        for eid, title in get_events(query):
            btn = Button(text=str(title), size_hint_y=None, height=dp(40),
                         background_normal='', background_color=theme['list_item_bg'],
                         color=theme['text'])
            btn.bind(on_press=partial(self.show_event_details, eid))
            self.event_list_layout.add_widget(btn)

    def populate_place_list(self, query=""):
        self.place_list_layout.clear_widgets()
        theme = THEMES[App.get_running_app().current_theme]
        for pid, name in get_places(query):
            btn = Button(text=str(name), size_hint_y=None, height=dp(40),
                         background_normal='', background_color=theme['list_item_bg'],
                         color=theme['text'])
            btn.bind(on_press=partial(self.show_place_details, pid))
            self.place_list_layout.add_widget(btn)

    def show_person_details(self, pid, _):
        PersonDetailsPopup(person_id=pid, on_save_callback=self.populate_person_list).open()

    def show_event_details(self, eid, _):
        EventDetailsPopup(event_id=eid, on_save_callback=self.populate_event_list).open()

    def show_place_details(self, pid, _):
        PlaceDetailsPopup(place_id=pid, on_save_callback=self.populate_place_list).open()

    def add_new_person(self, _):
        PersonDetailsPopup(person_id=None, on_save_callback=self.populate_person_list).open()

    def add_new_event(self, _):
        EventDetailsPopup(event_id=None, on_save_callback=self.populate_event_list).open()

    def add_new_place(self, _):
        PlaceDetailsPopup(place_id=None, on_save_callback=self.populate_place_list).open()

    def on_enter(self, *args):
        app = App.get_running_app()
        self.profile_button.text = f"Профиль: {app.user_name}"
        self.populate_person_list()
        self.populate_event_list()
        self.populate_place_list()
        self.update_theme()

    def update_theme(self):
        theme = THEMES[App.get_running_app().current_theme]
        self.layout.canvas.before.clear()
        with self.layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*theme['bg'])
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.layout.bind(size=self._update_rect, pos=self._update_rect)
        for w in self.walk():
            if isinstance(w, Label): w.color = theme['text']
            if isinstance(w, TextInput):
                w.background_color, w.foreground_color = theme['input_bg'], theme['text']
            if isinstance(w, Button) and w not in (
                    self.person_list_layout.children + self.event_list_layout.children + self.place_list_layout.children):
                w.background_color, w.color = theme['primary'], theme['button_text']

    def _update_rect(self, i, v):
        self.rect.pos, self.rect.size = i.pos, i.size

# ------------------- ЭКРАН ПРОФИЛЯ -------------------
class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        title = Label(text="Профиль и настройки", font_size='24sp', bold=True,
                      size_hint_y=None, height=dp(40))
        settings_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.5)
        settings_grid.add_widget(Label(text="Ваше имя (ФИО):"))
        self.name_input = TextInput(multiline=False)
        settings_grid.add_widget(self.name_input)
        settings_grid.add_widget(Label())
        save_btn = Button(text="Сохранить имя", on_press=self.save_name)
        settings_grid.add_widget(save_btn)
        settings_grid.add_widget(Label(text="Цветовая тема:"))
        theme_box = BoxLayout(spacing=dp(10))
        self.light_btn = ToggleButton(text="Светлая", group='theme',
                                      on_press=lambda _: self.change_theme('Светлая'))
        self.dark_btn = ToggleButton(text="Тёмная", group='theme',
                                     on_press=lambda _: self.change_theme('Тёмная'))
        theme_box.add_widget(self.light_btn)
        theme_box.add_widget(self.dark_btn)
        settings_grid.add_widget(theme_box)
        info_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.3)
        info_grid.add_widget(Label(text="Записей в базе:"))
        self.stats_label = Label(text="", bold=True)
        info_grid.add_widget(self.stats_label)
        about_btn = Button(text="О программе", on_press=self.show_about_popup)
        info_grid.add_widget(about_btn)
        self.status_label = Label(text="")
        info_grid.add_widget(self.status_label)
        back_btn = Button(text="< Назад на главный экран", size_hint_y=None, height=dp(50),
                          on_press=self.go_to_main)
        self.layout.add_widget(title)
        self.layout.add_widget(settings_grid)
        self.layout.add_widget(info_grid)
        self.layout.add_widget(back_btn)
        self.add_widget(self.layout)

    def on_enter(self, *args):
        app = App.get_running_app()
        self.name_input.text = app.user_name
        self.stats_label.text = f"{count_persons()} личностей | {count_events()} событий | {count_places()} мест"
        self.status_label.text = ""
        self.update_theme()

    def update_theme(self):
        app = App.get_running_app()
        theme = THEMES[app.current_theme]
        self.light_btn.state = 'down' if app.current_theme == 'Светлая' else 'normal'
        self.dark_btn.state = 'down' if app.current_theme == 'Тёмная' else 'normal'
        self.layout.canvas.before.clear()
        with self.layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*theme['bg'])
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.layout.bind(size=self._update_rect, pos=self._update_rect)
        for w in self.walk():
            if isinstance(w, Label): w.color = theme['text']
            if isinstance(w, (Button, ToggleButton)):
                w.background_color, w.color = theme['primary'], theme['button_text']

    def _update_rect(self, i, v):
        self.rect.pos, self.rect.size = i.pos, i.size

    def change_theme(self, name):
        App.get_running_app().change_theme(name)

    def save_name(self, _):
        name = self.name_input.text.strip()
        if name:
            App.get_running_app().set_user_name(name)
            self.status_label.text = "Имя сохранено!"
        else:
            self.status_label.text = "Имя не может быть пустым."

    def show_about_popup(self, _):
        Popup(title='О программе', size_hint=(0.7, 0.5),
              content=Label(text='Историческая Википедия v2.0\nСоздано с помощью Kivy и Python.')).open()

    def go_to_main(self, _):
        self.manager.current = 'main'

# ------------------- ПРИЛОЖЕНИЕ -------------------
class HistoryApp(App):
    def build(self):
        self.title = "Историческая Википедия"
        self.user_name = get_setting('user_name', 'Пользователь')
        self.current_theme = get_setting('theme', 'Тёмная')
        sm = ScreenManager(transition=FadeTransition())
        self.main_screen = MainScreen(name='main')
        self.profile_screen = ProfileScreen(name='profile')
        sm.add_widget(self.main_screen)
        sm.add_widget(self.profile_screen)
        Window.clearcolor = THEMES[self.current_theme]['bg']
        return sm

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        save_setting('theme', theme_name)
        Window.clearcolor = THEMES[self.current_theme]['bg']
        self.main_screen.update_theme()
        self.profile_screen.update_theme()

    def set_user_name(self, new_name):
        self.user_name = new_name
        save_setting('user_name', new_name)
        self.main_screen.profile_button.text = f"Профиль: {self.user_name}"

if __name__ == '__main__':
    HistoryApp().run()


# ------------------- ЭКРАН ПРОФИЛЯ -------------------
class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))

        title = Label(text="Профиль и настройки", font_size='24sp', bold=True,
                      size_hint_y=None, height=dp(40))

        settings_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.5)
        settings_grid.add_widget(Label(text="Ваше имя (ФИО):"))
        self.name_input = TextInput(multiline=False)
        settings_grid.add_widget(self.name_input)

        settings_grid.add_widget(Label())
        save_btn = Button(text="Сохранить имя", on_press=self.save_name)
        settings_grid.add_widget(save_btn)

        settings_grid.add_widget(Label(text="Цветовая тема:"))
        theme_box = BoxLayout(spacing=dp(10))
        self.light_btn = ToggleButton(text="Светлая", group='theme',
                                      on_press=lambda _: self.change_theme('Светлая'))
        self.dark_btn = ToggleButton(text="Тёмная", group='theme',
                                     on_press=lambda _: self.change_theme('Тёмная'))
        theme_box.add_widget(self.light_btn)
        theme_box.add_widget(self.dark_btn)
        settings_grid.add_widget(theme_box)

        info_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.3)
        info_grid.add_widget(Label(text="Записей в базе:"))
        self.stats_label = Label(text="", bold=True)
        info_grid.add_widget(self.stats_label)

        about_btn = Button(text="О программе", on_press=self.show_about_popup)
        info_grid.add_widget(about_btn)
        self.status_label = Label(text="")
        info_grid.add_widget(self.status_label)

        back_btn = Button(text="< Назад на главный экран", size_hint_y=None, height=dp(50),
                          on_press=self.go_to_main)

        self.layout.add_widget(title)
        self.layout.add_widget(settings_grid)
        self.layout.add_widget(info_grid)
        self.layout.add_widget(back_btn)
        self.add_widget(self.layout)

    def on_enter(self, *args):
        app = App.get_running_app()
        self.name_input.text = app.user_name
        self.stats_label.text = f"{count_persons()} личностей | {count_events()} событий | {count_places()} мест"
        self.status_label.text = ""
        self.update_theme()

    def update_theme(self):
        app = App.get_running_app()
        theme = THEMES[app.current_theme]
        self.light_btn.state = 'down' if app.current_theme == 'Светлая' else 'normal'
        self.dark_btn.state  = 'down' if app.current_theme == 'Тёмная'  else 'normal'

        self.layout.canvas.before.clear()
        with self.layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*theme['bg'])
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.layout.bind(size=self._update_rect, pos=self._update_rect)

        for w in self.walk():
            if isinstance(w, Label): w.color = theme['text']
            if isinstance(w, (Button, ToggleButton)):
                w.background_color, w.color = theme['primary'], theme['button_text']

    def _update_rect(self, i, v):
        self.rect.pos, self.rect.size = i.pos, i.size

    def change_theme(self, name):
        App.get_running_app().change_theme(name)

    def save_name(self, _):
        name = self.name_input.text.strip()
        if name:
            App.get_running_app().set_user_name(name)
            self.status_label.text = "Имя сохранено!"
        else:
            self.status_label.text = "Имя не может быть пустым."

    def show_about_popup(self, _):
        Popup(title='О программе', size_hint=(0.7, 0.5),
              content=Label(text='Историческая Википедия v2.0\nСоздано с помощью Kivy и Python.')).open()

    def go_to_main(self, _):
        self.manager.current = 'main'


# ------------------- ПРИЛОЖЕНИЕ -------------------
class HistoryApp(App):
    def build(self):
        self.title = "Историческая Википедия"
        self.user_name = get_setting('user_name', 'Пользователь')
        self.current_theme = get_setting('theme', 'Тёмная')

        sm = ScreenManager(transition=FadeTransition())
        self.main_screen = MainScreen(name='main')
        self.profile_screen = ProfileScreen(name='profile')
        sm.add_widget(self.main_screen)
        sm.add_widget(self.profile_screen)

        Window.clearcolor = THEMES[self.current_theme]['bg']
        return sm

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        save_setting('theme', theme_name)
        Window.clearcolor = THEMES[self.current_theme]['bg']
        self.main_screen.update_theme()
        self.profile_screen.update_theme()

    def set_user_name(self, new_name):
        self.user_name = new_name
        save_setting('user_name', new_name)
        self.main_screen.profile_button.text = f"Профиль: {self.user_name}"

if __name__ == '__main__':
    HistoryApp().run()