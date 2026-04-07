package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHelloEndpoint_Unit(t *testing.T) {
	req := httptest.NewRequest("GET", "/api/hello", nil)
	w := httptest.NewRecorder()

	helloHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("ожидался статус 200, получен %d", w.Code)
	}
}

func TestHelloEndpoint_Integration(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(helloHandler))
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/api/hello")
	if err != nil {
		t.Fatalf("failed to make request: %v", err)
	}

	if closeErr := resp.Body.Close(); closeErr != nil {
		t.Logf("warning: failed to close response body: %v", closeErr)
	}

	if resp.StatusCode != http.StatusOK {
		t.Errorf("ожидался статус 200, получен %d", resp.StatusCode)
	}
}
