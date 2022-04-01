from fastapi import HTTPException, status

TOKEN_EXC = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid auth token")
AUTH_EXC = HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
CRED_EXC = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Credentials are not valid")
LANG_EXC = HTTPException(status_code=status.HTTP_306_RESERVED, detail="Language doesn't exist")
NAME_EXC = HTTPException(status_code=status.HTTP_306_RESERVED, detail="Track name isn't avaluable")
RECORD_EXC = HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Record is not found")
ACCESS_EXC = HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="No access")
EMAIL_EXC = HTTPException(status_code=status.HTTP_306_RESERVED, detail="Email is already used")
PASS_EXC = HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Wrong password")