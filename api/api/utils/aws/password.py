import random

SPECIAL_CHARACTERS = '(^$*.[]{}()?-"!@#%&/\\,><\':;|_~`+=)'

'''
Password requirements
Contains at least 1 number
Contains at least 1 special character (^ $ * . [ ] { } ( ) ? - " ! @ # % & / \ , > < ' : ; | _ ~ ` + =)
Contains at least 1 uppercase letter
Contains at least 1 lowercase letter

Password minimum length
8 character(s)

'''

def generate_aws_compliant_password():
    rand_numbers = str(generate_number())
    rand_special_characters = generate_special_characters()
    rand_uppercase_letter = generate_lowercase_characters(1).upper()
    rand_lowercase_letter = generate_lowercase_characters(1)
    rand_characters = generate_lowercase_characters(8)

    full_un_shuffled = rand_numbers+rand_special_characters+rand_uppercase_letter+rand_lowercase_letter+rand_characters
    
    return ''.join(random.sample(full_un_shuffled, len(full_un_shuffled)))

def generate_number(max_length=5):
    return random.randrange(0, 10**max_length)

def generate_lowercase_characters(length=5):
    result = ''
    for _ in range(length):
        chr_id = random.randrange(97, 122+1)
        result += chr(chr_id)
    return result

def generate_special_characters(length=5):
    result = ''
    for _ in range(length):
        result += random.choice(SPECIAL_CHARACTERS)
    return result

if __name__ == '__main__':
    print(generate_aws_compliant_password())
