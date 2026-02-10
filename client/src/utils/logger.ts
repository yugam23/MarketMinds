type LogLevel = "debug" | "info" | "warn" | "error";

class Logger {
  private shouldLog(level: LogLevel): boolean {
    if (import.meta.env.PROD && level === "debug") return false;
    return true;
  }

  debug(message: string, ...args: any[]) {
    if (this.shouldLog("debug")) {
      console.log(`[DEBUG] ${message}`, ...args);
    }
  }

  info(message: string, ...args: any[]) {
    if (this.shouldLog("info")) {
      console.info(`[INFO] ${message}`, ...args);
    }
  }

  warn(message: string, ...args: any[]) {
    if (this.shouldLog("warn")) {
      console.warn(`[WARN] ${message}`, ...args);
    }
  }

  error(message: string, error?: Error | unknown) {
    if (this.shouldLog("error")) {
      console.error(`[ERROR] ${message}`, error);
      // In a real app, we would send this to Sentry/LogRocket here
      if (import.meta.env.PROD) {
        // captureException(error);
      }
    }
  }
}

export const logger = new Logger();
