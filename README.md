# Система разграничения прав доступа (Access Control System)

## Общее описание

Разработанная система управления доступом представляет собой гибридную модель, сочетающую в себе **RBAC** (Role-Based Access Control - управление доступом на основе ролей) и **ABAC** (Attribute-Based Access Control - управление доступом на основе атрибутов). 

Ключевая особенность системы - **правила доступа хранятся непосредственно в базе данных** и могут быть изменены администратором в режиме реального времени без перезапуска приложения или изменения кода.

## Основные принципы работы

### 1. Трехуровневая модель доступа

Система использует три уровня проверки доступа:

| Уровень | Описание | Принятие решения |
|---------|----------|------------------|
| **Уровень 1: Глобальный доступ** | Проверка суперпользователя | Если пользователь - суперпользователь, доступ разрешается немедленно |
| **Уровень 2: Ролевой доступ** | Проверка прав через роли | Система проверяет, есть ли у роли пользователя необходимые разрешения |
| **Уровень 3: Объектный доступ** | Проверка на уровне конкретного объекта | Применяются фильтры и условия из правил доступа |

### 2. Компоненты системы

#### 2.1 Пользователь (User)
- **Идентификация**: по уникальному email
- **Атрибуты**: 
  - `email` - уникальный идентификатор
  - `full_name` - полное имя
  - `department` - отдел (используется в правилах)
  - `is_active` - статус активности
  - `is_staff` - доступ к админке

#### 2.2 Роль (Role)
- **Назначение**: группа пользователей с одинаковыми правами
- **Скоупы (области видимости)**:
  - **GLOBAL** - полный доступ ко всем ресурсам системы
  - **DEPARTMENT** - доступ только к ресурсам своего отдела
  - **OWNER** - доступ только к своим объектам
  - **CUSTOM** - доступ по кастомным правилам (условиям)

#### 2.3 Разрешение (Permission)
- **Формат**: `{resource_type}:{action}`
- **Примеры**:
  - `project:read` - чтение проектов
  - `project:create` - создание проектов
  - `project:update` - обновление проектов
  - `project:delete` - удаление проектов
  - `task:read` - чтение задач
  - `user:manage` - управление пользователями

#### 2.4 Правило доступа (AccessRule)
- **Самый важный компонент системы**
- **Структура**:
  ```json
  {
    "id": 1,
    "role": 3,
    "resource_type": "project",
    "action": "read",
    "filter_condition": {"owner_id": "{{user.id}}"},
    "is_active": true,
    "priority": 10
  }



## Архитектура БД

```mermaid
erDiagram
    User ||--o{ UserRole : имеет
    User ||--o{ AccessAuditLog : создает
    
    Role ||--o{ UserRole : назначена
    Role ||--o{ RolePermission : включает
    Role ||--o{ AccessRule : определяет
    
    Permission ||--o{ RolePermission : содержит
    
    User {
        int id PK
        varchar email
        varchar full_name
        varchar department
        boolean is_active
        boolean is_staff
        timestamp date_joined
    }
    
    Role {
        int id PK
        varchar name
        text description
        varchar scope
    }
    
    Permission {
        int id PK
        varchar name
        varchar resource_type
        varchar action
    }
    
    UserRole {
        int id PK
        int user_id FK
        int role_id FK
        timestamp assigned_at
    }
    
    RolePermission {
        int id PK
        int role_id FK
        int permission_id FK
    }
    
    AccessRule {
        int id PK
        int role_id FK
        varchar resource_type
        varchar action
        jsonb filter_condition
        boolean is_active
        int priority
    }
    
    AccessAuditLog {
        int id PK
        int user_id FK
        varchar resource_type
        varchar action
        boolean decision
        text reason
        timestamp created_at
    }



## АЛГОРИТМ ПРОВЕРКИ ДОСТУПА
```mermaid

flowchart TD
    Start([ПРИХОДИТ ЗАПРОС]) --> Step1[1. Проверяем токен]
    
    Step1 --> Q1{Токен верный?}
    Q1 -->|Нет| Error1[ 401 - Не авторизован]
    Q1 -->|Да| Step2[2. Получаем пользователя]
    
    Step2 --> Q2{Это суперпользователь?}
    Q2 -->|Да| Success[ ДОСТУП ЕСТЬ]
    Q2 -->|Нет| Step3[3. Ищем роли пользователя]
    
    Step3 --> Q3{Роли есть?}
    Q3 -->|Нет| Error2[ 403 - Нет прав]
    Q3 -->|Да| Step4[4. Ищем правила доступа]
    
    Step4 --> Q4{Правила есть?}
    Q4 -->|Нет| Error2
    Q4 -->|Да| Step5[5. Проверяем правила по очереди]
    
    Step5 --> Check1{Правило GLOBAL?}
    Check1 -->|Да| Success
    
    Check1 -->|Нет| Check2{Правило DEPARTMENT?}
    Check2 -->|Да| Q5{Отдел совпадает?}
    Q5 -->|Да| Success
    Q5 -->|Нет| Next1[Смотрим следующее правило]
    
    Check2 -->|Нет| Check3{Правило OWNER?}
    Check3 -->|Да| Q6{Владелец совпадает?}
    Q6 -->|Да| Success
    Q6 -->|Нет| Next1
    
    Check3 -->|Нет| Check4{Правило CUSTOM?}
    Check4 -->|Да| Q7{Условия выполнены?}
    Q7 -->|Да| Success
    Q7 -->|Нет| Next1
    
    Check4 -->|Нет| Next1
    
    Next1 --> Q8{Еще правила есть?}
    Q8 -->|Да| Step5
    Q8 -->|Нет| Error2
    
    Success --> Log[📝 Запись в лог: Разрешено]
    Error2 --> Log2[📝 Запись в лог: Запрещено]
    Error1 --> End([КОНЕЦ])
    
    Log --> End
    Log2 --> End
