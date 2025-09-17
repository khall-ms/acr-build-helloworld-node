using System;
using System.Collections.Generic;

namespace SampleProject
{
    public class UserService
    {
        private readonly IUserRepository _userRepository;
        
        public UserService(IUserRepository userRepository)
        {
            _userRepository = userRepository;
        }
        
        public User GetUser(int id)
        {
            return _userRepository.FindById(id);
        }
        
        public void CreateUser(User user)
        {
            _userRepository.Save(user);
        }
    }
    
    public interface IUserRepository
    {
        User FindById(int id);
        void Save(User user);
        List<User> GetAll();
    }
    
    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        
        public User()
        {
        }
        
        public User(string name, string email)
        {
            Name = name;
            Email = email;
        }
    }
}