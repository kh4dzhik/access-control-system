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
  

```mermaid
erDiagram
    User ||--o{ UserRole : has
    User ||--o{ AccessAuditLog : creates
    User ||--o{ AccessRule : "created by"
    
    Role ||--o{ UserRole : assigned
    Role ||--o{ RolePermission : includes
    Role ||--o{ AccessRule : defines
    
    Permission ||--o{ RolePermission : "belongs to"
    
    AccessRule ||--o{ AccessAuditLog : "logged in"
    
    User {
        int id PK
        varchar email UK
        varchar full_name
        varchar department
        boolean is_active
        boolean is_staff
        timestamp date_joined
    }
    
    Role {
        int id PK
        varchar name UK
        text description
        varchar scope "GLOBAL/DEPARTMENT/OWNER/CUSTOM"
    }
    
    Permission {
        int id PK
        varchar name UK
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
        varchar resource_id
        varchar action
        boolean decision
        text reason
        inet ip_address
        timestamp created_at
    }
