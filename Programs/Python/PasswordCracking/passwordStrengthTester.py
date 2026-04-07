#!/usr/bin/env python3
"""
Password Strength Tester - Ethical Security Tool
For educational purposes and testing your own passwords only.
"""

import hashlib
import time
import argparse
import sys
from pathlib import Path
import itertools
import string

class PasswordTester:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.attempts = 0
        self.start_time = None
        
    def hash_password(self, password, hash_type='md5'):
        """Generate hash of password"""
        if hash_type == 'md5':
            return hashlib.md5(password.encode()).hexdigest()
        elif hash_type == 'sha1':
            return hashlib.sha1(password.encode()).hexdigest()
        elif hash_type == 'sha256':
            return hashlib.sha256(password.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash type: {hash_type}")
    
    def dictionary_attack(self, target_hash, wordlist_path, hash_type='md5'):
        """Perform dictionary attack using wordlist"""
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for word in f:
                    word = word.strip()
                    self.attempts += 1
                    
                    if self.verbose and self.attempts % 1000 == 0:
                        print(f"[*] Attempts: {self.attempts}, trying: {word}")
                    
                    if self.hash_password(word, hash_type) == target_hash:
                        return word
        except FileNotFoundError:
            print(f"[!] Wordlist not found: {wordlist_path}")
            return None
        
        return None
    
    def brute_force_attack(self, target_hash, max_length=4, hash_type='md5', 
                           charset=string.ascii_lowercase + string.digits):
        """Perform brute force attack up to specified length"""
        for length in range(1, max_length + 1):
            print(f"[*] Trying passwords of length {length}...")
            
            for attempt in itertools.product(charset, repeat=length):
                password = ''.join(attempt)
                self.attempts += 1
                
                if self.verbose and self.attempts % 10000 == 0:
                    print(f"[*] Attempts: {self.attempts}")
                
                if self.hash_password(password, hash_type) == target_hash:
                    return password
        
        return None
    
    def common_passwords_attack(self, target_hash, hash_type='md5'):
        """Test against common passwords"""
        common_passwords = [
            "password", "123456", "12345678", "qwerty", "abc123",
            "monkey", "letmein", "dragon", "baseball", "master",
            "admin", "welcome", "shadow", "sunshine", "password1"
        ]
        
        for password in common_passwords:
            self.attempts += 1
            if self.hash_password(password, hash_type) == target_hash:
                return password
        
        return None
    
    def test_password_strength(self, password):
        """Evaluate password strength and provide feedback"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 12:
            score += 2
            feedback.append("✓ Good length (12+ characters)")
        elif len(password) >= 8:
            score += 1
            feedback.append("⚠️ Minimum length (8-11 characters)")
        else:
            feedback.append("❌ Too short (less than 8 characters)")
        
        # Character variety checks
        if any(c.islower() for c in password):
            score += 1
            feedback.append("✓ Contains lowercase letters")
        
        if any(c.isupper() for c in password):
            score += 1
            feedback.append("✓ Contains uppercase letters")
        
        if any(c.isdigit() for c in password):
            score += 1
            feedback.append("✓ Contains numbers")
        
        if any(c in string.punctuation for c in password):
            score += 1
            feedback.append("✓ Contains special characters")
        
        # Common password check
        if password.lower() in ["password", "123456", "qwerty", "admin"]:
            score -= 2
            feedback.append("❌ Avoid using common passwords")
        
        # Provide rating
        print("\n" + "="*50)
        print("PASSWORD STRENGTH ANALYSIS")
        print("="*50)
        for f in feedback:
            print(f)
        
        print("\nStrength Score: {}/6".format(score))
        
        if score >= 5:
            rating = "STRONG ✓"
        elif score >= 3:
            rating = "MODERATE ⚠️"
        else:
            rating = "WEAK ❌"
        
        print(f"Overall Rating: {rating}")
        return score

def main():
    parser = argparse.ArgumentParser(description='Ethical Password Strength Tester')
    parser.add_argument('-t', '--test', help='Test password strength')
    parser.add_argument('-c', '--crack', help='Hash to crack (for testing)')
    parser.add_argument('-H', '--hash-type', default='md5', 
                        choices=['md5', 'sha1', 'sha256'], 
                        help='Hash algorithm')
    parser.add_argument('-w', '--wordlist', help='Wordlist file for dictionary attack')
    parser.add_argument('-b', '--brute-force', type=int, 
                        help='Max length for brute force attack')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='Verbose output')
    
    args = parser.parse_args()
    
    tester = PasswordTester(verbose=args.verbose)
    
    if args.test:
        # Test password strength
        tester.test_password_strength(args.test)
        
    elif args.crack:
        # Attempt to crack hash
        print(f"[*] Attempting to crack hash: {args.crack}")
        print(f"[*] Hash type: {args.hash_type}")
        
        # Try common passwords first
        print("\n[*] Trying common passwords...")
        result = tester.common_passwords_attack(args.crack, args.hash_type)
        
        if result:
            print(f"\n[+] Password found! (common passwords): {result}")
            print(f"[+] Total attempts: {tester.attempts}")
            return
        
        # Try dictionary attack if wordlist provided
        if args.wordlist:
            print(f"\n[*] Performing dictionary attack with: {args.wordlist}")
            result = tester.dictionary_attack(args.crack, args.wordlist, args.hash_type)
            
            if result:
                print(f"\n[+] Password found! (dictionary): {result}")
                print(f"[+] Total attempts: {tester.attempts}")
                return
        
        # Try brute force if specified
        if args.brute_force:
            print(f"\n[*] Performing brute force attack (max length: {args.brute_force})")
            print("[!] This may take a long time for longer passwords!")
            result = tester.brute_force_attack(
                args.crack, 
                args.brute_force, 
                args.hash_type
            )
            
            if result:
                print(f"\n[+] Password found! (brute force): {result}")
                print(f"[+] Total attempts: {tester.attempts}")
                return
        
        print(f"\n[-] Password not found after {tester.attempts} attempts")
        
    else:
        # Interactive mode
        print("="*50)
        print("ETHICAL PASSWORD STRENGTH TESTER")
        print("="*50)
        print("\nThis tool is for educational purposes only.")
        print("Only test passwords that you own or have permission to test.\n")
        
        while True:
            print("\nOptions:")
            print("1. Test password strength")
            print("2. Generate hash")
            print("3. Exit")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == '1':
                password = input("Enter password to test: ")
                tester.test_password_strength(password)
                
                # Optional: Show hash
                show_hash = input("\nShow hash? (y/n): ").lower()
                if show_hash == 'y':
                    hash_type = input("Hash type (md5/sha1/sha256): ").lower()
                    if hash_type in ['md5', 'sha1', 'sha256']:
                        print(f"\n{hash_type.upper()} hash: {tester.hash_password(password, hash_type)}")
            
            elif choice == '2':
                password = input("Enter password to hash: ")
                print(f"\nMD5: {tester.hash_password(password, 'md5')}")
                print(f"SHA1: {tester.hash_password(password, 'sha1')}")
                print(f"SHA256: {tester.hash_password(password, 'sha256')}")
            
            elif choice == '3':
                print("Exiting...")
                break
            
            else:
                print("Invalid option")

if __name__ == "__main__":
    main()
