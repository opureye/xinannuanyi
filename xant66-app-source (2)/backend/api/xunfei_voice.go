@hosturl :  like  	wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6
@apikey : f66675d186c7c097f608c057bed85803
@apiSecret : YWYzYmE0ZTg5NGIxOTIwZjQ5ZDk2NzY1
@APPID : 2f4bc0cc
    func assembleAuthUrl(hosturl string, apiKey, apiSecret string) string {
        ul, err := url.Parse(hosturl)
        if err != nil {
            fmt.Println(err)
        }
        //签名时间
        date := time.Now().UTC().Format(time.RFC1123)
        //参与签名的字段 host ,date, request-line
        signString := []string{"host: " + ul.Host, "date: " + date, "GET " + ul.Path + " HTTP/1.1"}
        //拼接签名字符串
        sgin := strings.Join(signString, "\n")
        //签名结果
        sha := HmacWithShaTobase64("hmac-sha256", sgin, apiSecret)
        //构建请求参数 此时不需要urlencoding
        authUrl := fmt.Sprintf("api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"", apiKey,
            "hmac-sha256", "host date request-line", sha)
        //将请求参数使用base64编码
        authorization:= base64.StdEncoding.EncodeToString([]byte(authUrl))
        v := url.Values{}
        v.Add("host", ul.Host)
        v.Add("date", date)
        v.Add("authorization", authorization)
        //将编码后的字符串url encode后添加到url后面
        callurl := hosturl + "?" + v.Encode()
        return callurl
    }