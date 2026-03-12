const LOCAL_USER = {
  username: "local-user",
  userId: "local-user",
  given_name: "Local",
  family_name: "User",
};

export const signIn = async () => LOCAL_USER;

export const logOut = async () => null;

export const getUser = async () => LOCAL_USER;

export const getSession = async () => ({ tokens: null });
