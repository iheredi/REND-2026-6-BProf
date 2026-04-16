const FLASH_KEY = "flash";

export const setFlash = (msg) => {
    sessionStorage.setItem(FLASH_KEY, msg);
};

export const consumeFlash = () => {
    const msg = sessionStorage.getItem(FLASH_KEY);
    sessionStorage.removeItem(FLASH_KEY);
    return msg;
};