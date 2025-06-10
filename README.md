# Springboard_Capstone_1_Project: 

**Title:** FoodieFinds: Recipe Finder App & Blog  
**Deployment URL:** https://foodiefinds-recipe-finder.onrender.com  
**API:** Spoontacular API: https://spoonacular.com/food-api  

## Description
FoodieFinds is a web application designed to simplify the cooking experience by helping users discover recipes based on available ingredients, personal preferences, and dietary restrictions. Whether you're a novice cook or a culinary enthusiast, FoodieFinds aims to provide a user-friendly platform for finding, saving, and even creating your own recipes.

## Implemented Features and Rationale
1. **Recipe Generator:** Once logging in, users will be directed to the home page, where 10 random recipes will populate. If the user has set any dietary preferences or allergies, the recipes populated will be in alignment with those.
   
2. **Recipe Search:** Users can search for recipes based on available ingredients, recipe names, or explore random recipes for inspiration. This feature provides flexibility for users with varying needs and preferences.
   
3. **Favorite Recipes:** Users can save their favorite recipes for quick and easy access during future cooking sessions. This feature enhances user engagement and retention, as users can build a personalized collection of go-to recipes.

4. **Recipe Creation:** Empowering users to save and edit their own recipes adds a personal touch to the app. This feature caters to individuals who enjoy experimenting in the kitchen and allows them to customize ingredients and cooking instructions.

5. **User Authentication:** Users can create accounts and log in to access personalized features. This not only secures user data but also enables the app to provide a customized experience based on individual preferences.

## User Flow
1. **Registration/Login:** Users start by creating an account or logging in to access personalized features.
   
2. **Homepage:** Upon logging in, users land on the homepage featuring a list of 10 random recipes. If the user has set any dietary preferences or allergies, the recipes populated will be in alignment with those.

3. **Recipe Search:** Users can explore recipes based on ingredients or names, sparking inspiration for their next meal.

4. **Favorite Recipes:** Users can save recipes they love for quick access during future cooking sessions.

5. **Recipe Creation:** For those feeling adventurous, users can create and customize their own recipes, tailoring them to personal preferences.

6. **User Preferences:** Users can add any dietary preferences or allergies and the recipes they find will align to these automatically.

## API Notes
The app relies on the Spoonacular API to provide a comprehensive recipe database. While using this external API, the biggest issue is the limitation of the amount of API calls per day as I have a free API Key. That being said, the app can crash if too many calls are made. Also, I had to include the API_KEY in the Render Deployment which is not the best practice, security-wise.

## Technology Stack
- **Python**
- **Flask** (Web Framework)
- **Spoonacular API** (Primary Data Source)
- **PostgreSQL** (Database)
- **Flask-Bcrypt** (Password Hashing for Security)


