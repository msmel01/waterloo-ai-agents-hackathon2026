import Axios, { AxiosRequestConfig } from 'axios';

export const AXIOS_INSTANCE = Axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

let authToken: string | null = null;
let authTokenProvider: (() => Promise<string | null>) | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

export function setAuthTokenProvider(provider: (() => Promise<string | null>) | null) {
  authTokenProvider = provider;
}

AXIOS_INSTANCE.interceptors.request.use(async (config) => {
  const requestUrl = config.url ?? '';
  const needsSuitorAuth =
    requestUrl.startsWith('/api/v1/suitors') || requestUrl.startsWith('/api/v1/sessions');

  if (!authToken && needsSuitorAuth && authTokenProvider) {
    try {
      authToken = await authTokenProvider();
    } catch {
      authToken = null;
    }
  }

  if (authToken) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

export const customInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  const source = Axios.CancelToken.source();
  const promise = AXIOS_INSTANCE({
    ...config,
    cancelToken: source.token,
  }).then(({ data }) => data);

  // @ts-expect-error orval cancellation hook
  promise.cancel = () => {
    source.cancel('Query was cancelled');
  };

  return promise;
};

export default customInstance;
