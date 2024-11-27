package main

import (
    "testing"
    "github.com/stretchr/testify/assert"
)
type SetupAllSuite interface {
	SetupSuite()
}
func TestStatusNotDown(t *testing.T) {
	assert.NotEqual(t, status, "down")
  }
  func (suite *ExampleTestSuite) SetupTest() {
    WakuSetup()
  config := WakuConfig{
		Host:        "0.0.0.0",
		Port:        30304,
		NodeKey:     "11d0dcea28e86f81937a3bd1163473c7fbc0a0db54fd72914849bc47bdf78710",
		EnableRelay: true,
		LogLevel:    "DEBUG",
	}
  node,err := WakuNew(config)
  assert.NotEqual(t, err, nil)
}

