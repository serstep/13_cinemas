from bs4 import BeautifulSoup
import requests, time, argparse


def fetch_afisha_page():
    response = requests.get("http://www.afisha.ru/msk/schedule_cinema/")
    return response.content


def parse_afisha_list(raw_html):
    """In the end of the function I use sort by theaters. 
    I do it to get more popular movies first of all, because 
    kinopoisk.ru can block access to site when script is working.
    """
    afisha_soup = BeautifulSoup(raw_html, "lxml")
    movies_tags = afisha_soup.find_all("div", class_="object")
    movies_info = []

    for movie_tag in movies_tags:
        movie_name = movie_tag.find("h3").text
        theaters_count = len(movie_tag.find_all("td", class_="b-td-item"))
        movies_info.append((movie_name, theaters_count))

    movies_info.sort(key=lambda movie: movie[1], reverse=True)
    return movies_info
        
    
def fetch_movie_info(movies_list):
    page_loading_timeout = 10
    page_timeout_reduce = 2
    unfetched_movies_counter = 0
    
    movies_rated_list = []

    for movie_name, theaters_count in movies_list:
        payload = {"first" : "yes", "what" : "", "kp_query" : movie_name }

        try:
            response = requests.get("https://www.kinopoisk.ru/index.php", \
                params=payload, timeout=page_loading_timeout)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            unfetched_movies_counter += 1
            page_loading_timeout /= page_timeout_reduce
            continue

        movie_soup = BeautifulSoup(response.content, "lxml")
        movie_rating_tag = movie_soup.find("span", class_="rating_ball")
        people_rate_count_tag = movie_soup.find("span", class_="ratingCount")

        if movie_rating_tag is None or people_rate_count_tag is None:
            unfetched_movies_counter += 1
            continue

        movies_rated_list.append((movie_name, int(theaters_count), \
            float(movie_rating_tag.text), people_rate_count_tag.text))

    return (movies_rated_list, unfetched_movies_counter)
        

def output_movies_to_console(movies_list):
    required_movies_count = 10

    movies_list.sort(key=lambda movie: movie[2], reverse=True)

    for movie_name, theaters_count, movie_rating, people_rate_count in movies_list[:required_movies_count]:
        print("Name: {}\nTheaters count: {}\nRating: {}\nVoters count: {}".format(\
            movie_name, theaters_count, movie_rating, people_rate_count))
        print()


if __name__ == '__main__':
    print("fetching afisha.ru...")
    raw_html = fetch_afisha_page()
    movies_list = parse_afisha_list(raw_html)

    print("fetching kinopoisk.ru...")
    movies_rated_list, unfetched_movies_number = fetch_movie_info(movies_list)

    if unfetched_movies_number > 0:
        print("Could not fetch {} movies ".format(unfetched_movies_number))

    if len(movies_rated_list) < 1:
        print("Can not fetch movies info")
        exit(1)

    output_movies_to_console(movies_rated_list)
