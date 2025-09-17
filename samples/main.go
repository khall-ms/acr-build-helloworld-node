package main

import (
    "fmt"
    "log"
    "net/http"
)

// User represents a user in the system
type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

// UserRepository handles user data operations
type UserRepository struct {
    users map[int]*User
}

// NewUserRepository creates a new user repository
func NewUserRepository() *UserRepository {
    return &UserRepository{
        users: make(map[int]*User),
    }
}

// Save stores a user in the repository
func (r *UserRepository) Save(user *User) error {
    if user.ID == 0 {
        user.ID = len(r.users) + 1
    }
    r.users[user.ID] = user
    return nil
}

// FindByID retrieves a user by ID
func (r *UserRepository) FindByID(id int) (*User, error) {
    user, exists := r.users[id]
    if !exists {
        return nil, fmt.Errorf("user not found")
    }
    return user, nil
}

// GetAll returns all users
func (r *UserRepository) GetAll() []*User {
    users := make([]*User, 0, len(r.users))
    for _, user := range r.users {
        users = append(users, user)
    }
    return users
}

// UserService provides business logic for user operations
type UserService struct {
    repo *UserRepository
}

// NewUserService creates a new user service
func NewUserService(repo *UserRepository) *UserService {
    return &UserService{repo: repo}
}

// CreateUser creates a new user
func (s *UserService) CreateUser(name, email string) (*User, error) {
    user := &User{
        Name:  name,
        Email: email,
    }
    
    err := s.repo.Save(user)
    if err != nil {
        return nil, err
    }
    
    return user, nil
}

// GetUser retrieves a user by ID
func (s *UserService) GetUser(id int) (*User, error) {
    return s.repo.FindByID(id)
}

func main() {
    repo := NewUserRepository()
    service := NewUserService(repo)
    
    // Create a sample user
    user, err := service.CreateUser("John Doe", "john@example.com")
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("Created user: %+v\n", user)
    
    // Start HTTP server
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("OK"))
    })
    
    log.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}